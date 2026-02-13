"""Integration tests for bug detection API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app
from app.core.oracle.bug_patterns import BugSeverity, BugCategory

client = TestClient(app)


class TestBugsAPI:
    """Test cases for bug detection API endpoints."""

    @pytest.fixture
    def sample_bugs(self):
        """Create sample bugs for testing."""
        return [
            {
                "bug_number": "13364795",
                "title": "Wrong results with optimizer_adaptive_features",
                "category": BugCategory.OPTIMIZER,
                "severity": BugSeverity.CRITICAL,
                "description": "Test bug description",
                "symptoms": ["Incorrect results", "Data inconsistency"],
                "affected_versions": ["12.1.0.1", "12.1.0.2"],
                "fixed_versions": ["12.2.0.1"],
                "workarounds": ["Set optimizer_adaptive_features=false"],
                "remediation_sql": "ALTER SESSION SET optimizer_adaptive_features=false;",
                "my_oracle_support_url": "https://support.oracle.com/bug/13364795",
            },
            {
                "bug_number": "19396364",
                "title": "Parallel query hangs",
                "category": BugCategory.PARALLEL,
                "severity": BugSeverity.HIGH,
                "description": "Parallel queries may hang",
                "symptoms": ["Query hangs", "No response"],
                "affected_versions": ["12.1.0.2"],
                "fixed_versions": ["12.2.0.1"],
                "workarounds": ["Disable parallel query"],
                "remediation_sql": None,
                "my_oracle_support_url": None,
            },
        ]

    def test_get_all_bugs_success(self, sample_bugs):
        """Test getting all bugs successfully."""
        with patch("app.services.bug_detection_service.BugDetectionService.get_all_bugs") as mock_get:
            mock_get.return_value = {
                "bugs": sample_bugs,
                "total_count": len(sample_bugs),
                "filters_applied": {},
            }

            response = client.get("/api/v1/bugs")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 2
            assert len(data["bugs"]) == 2
            assert data["bugs"][0]["bug_number"] == "13364795"

    def test_get_all_bugs_with_filters(self, sample_bugs):
        """Test getting bugs with filters."""
        filtered_bugs = [b for b in sample_bugs if b["severity"] == BugSeverity.CRITICAL]

        with patch("app.services.bug_detection_service.BugDetectionService.get_all_bugs") as mock_get:
            mock_get.return_value = {
                "bugs": filtered_bugs,
                "total_count": len(filtered_bugs),
                "filters_applied": {"severity": "critical"},
            }

            response = client.get("/api/v1/bugs?severity=critical")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 1
            assert data["bugs"][0]["severity"] == BugSeverity.CRITICAL

    def test_get_all_bugs_by_category(self, sample_bugs):
        """Test filtering bugs by category."""
        filtered_bugs = [b for b in sample_bugs if b["category"] == BugCategory.OPTIMIZER]

        with patch("app.services.bug_detection_service.BugDetectionService.get_all_bugs") as mock_get:
            mock_get.return_value = {
                "bugs": filtered_bugs,
                "total_count": len(filtered_bugs),
                "filters_applied": {"category": "optimizer"},
            }

            response = client.get("/api/v1/bugs?category=optimizer")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 1
            assert data["bugs"][0]["category"] == BugCategory.OPTIMIZER

    def test_get_all_bugs_by_version(self, sample_bugs):
        """Test filtering bugs by version."""
        with patch("app.services.bug_detection_service.BugDetectionService.get_all_bugs") as mock_get:
            mock_get.return_value = {
                "bugs": sample_bugs,
                "total_count": len(sample_bugs),
                "filters_applied": {"version": "12.1.0.1"},
            }

            response = client.get("/api/v1/bugs?version=12.1.0.1")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] >= 1

    def test_get_all_bugs_error(self):
        """Test error handling when getting all bugs."""
        with patch("app.services.bug_detection_service.BugDetectionService.get_all_bugs") as mock_get:
            mock_get.side_effect = Exception("Database error")

            response = client.get("/api/v1/bugs")

            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["code"] == "INTERNAL_ERROR"

    def test_detect_bugs_for_query_success(self, sample_bugs):
        """Test detecting bugs for a specific SQL_ID."""
        detection_result = {
            "sql_id": "abc123def4567",
            "detected_bugs": [
                {
                    "bug": sample_bugs[0],
                    "confidence": 85,
                    "matched_patterns": ["execution_plan", "parameters"],
                    "evidence": {
                        "execution_plan": {"operations_found": ["ADAPTIVE"]},
                        "parameters": {"optimizer_adaptive_features": {"expected": "true", "actual": "TRUE"}},
                    },
                    "sql_id": "abc123def4567",
                }
            ],
            "summary": {
                "total_bugs": 1,
                "by_severity": {"critical": 1},
                "by_category": {"optimizer": 1},
                "high_confidence_count": 1,
                "critical_count": 1,
            },
            "database_version": "12.1.0.1",
            "detection_timestamp": "2024-01-15T10:30:00",
        }

        with patch("app.services.bug_detection_service.BugDetectionService.detect_bugs_for_query") as mock_detect:
            mock_detect.return_value = detection_result

            response = client.get("/api/v1/bugs/abc123def4567")

            assert response.status_code == 200
            data = response.json()
            assert data["sql_id"] == "abc123def4567"
            assert len(data["detected_bugs"]) == 1
            assert data["detected_bugs"][0]["confidence"] == 85
            assert data["summary"]["total_bugs"] == 1

    def test_detect_bugs_for_query_with_version(self, sample_bugs):
        """Test detecting bugs with database version parameter."""
        detection_result = {
            "sql_id": "abc123def4567",
            "detected_bugs": [],
            "summary": {
                "total_bugs": 0,
                "by_severity": {},
                "by_category": {},
                "high_confidence_count": 0,
                "critical_count": 0,
            },
            "database_version": "19.0.0.0",
            "detection_timestamp": "2024-01-15T10:30:00",
        }

        with patch("app.services.bug_detection_service.BugDetectionService.detect_bugs_for_query") as mock_detect:
            mock_detect.return_value = detection_result

            response = client.get("/api/v1/bugs/abc123def4567?database_version=19.0.0.0")

            assert response.status_code == 200
            data = response.json()
            assert data["database_version"] == "19.0.0.0"
            assert data["summary"]["total_bugs"] == 0

    def test_detect_bugs_invalid_sql_id(self):
        """Test bug detection with invalid SQL_ID format."""
        # Too short
        response = client.get("/api/v1/bugs/abc123")
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_SQL_ID"

        # Too long
        response = client.get("/api/v1/bugs/abc123def456789")
        assert response.status_code == 400

        # Contains special characters
        response = client.get("/api/v1/bugs/abc123def45_7")
        assert response.status_code == 400

    def test_detect_bugs_query_not_found(self):
        """Test bug detection for non-existent query."""
        detection_result = {
            "sql_id": "notfound12345",
            "detected_bugs": [],
            "summary": {
                "total_bugs": 0,
                "by_severity": {},
                "by_category": {},
                "high_confidence_count": 0,
                "critical_count": 0,
            },
            "database_version": None,
            "detection_timestamp": "2024-01-15T10:30:00",
            "error": "Query not found",
        }

        with patch("app.services.bug_detection_service.BugDetectionService.detect_bugs_for_query") as mock_detect:
            mock_detect.return_value = detection_result

            response = client.get("/api/v1/bugs/notfound12345")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["code"] == "QUERY_NOT_FOUND"

    def test_check_version_bugs_success(self, sample_bugs):
        """Test checking bugs for a specific Oracle version."""
        version_result = {
            "database_version": "12.1.0.1",
            "bugs_affecting_version": sample_bugs,
            "total_count": 2,
            "critical_count": 1,
            "recommendation": "CRITICAL: 1 critical bugs affect version 12.1.0.1. Immediate patching or upgrade recommended.",
        }

        with patch("app.services.bug_detection_service.BugDetectionService.check_version_bugs") as mock_check:
            mock_check.return_value = version_result

            response = client.get("/api/v1/bugs/version/12.1.0.1")

            assert response.status_code == 200
            data = response.json()
            assert data["database_version"] == "12.1.0.1"
            assert data["total_count"] == 2
            assert data["critical_count"] == 1
            assert "CRITICAL" in data["recommendation"]
            assert len(data["bugs_affecting_version"]) == 2

    def test_check_version_bugs_no_bugs(self):
        """Test checking version with no bugs found."""
        version_result = {
            "database_version": "21.0.0.0",
            "bugs_affecting_version": [],
            "total_count": 0,
            "critical_count": 0,
            "recommendation": "No known bugs in database for version 21.0.0.0.",
        }

        with patch("app.services.bug_detection_service.BugDetectionService.check_version_bugs") as mock_check:
            mock_check.return_value = version_result

            response = client.get("/api/v1/bugs/version/21.0.0.0")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 0
            assert data["critical_count"] == 0
            assert "No known bugs" in data["recommendation"]

    def test_check_version_bugs_invalid_version(self):
        """Test checking bugs with invalid version format."""
        response = client.get("/api/v1/bugs/version/")

        # Should return 404 for empty version (route not found)
        assert response.status_code in [404, 422]

    def test_check_version_bugs_error(self):
        """Test error handling when checking version bugs."""
        with patch("app.services.bug_detection_service.BugDetectionService.check_version_bugs") as mock_check:
            mock_check.side_effect = Exception("Database error")

            response = client.get("/api/v1/bugs/version/12.1.0.1")

            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["code"] == "INTERNAL_ERROR"

    def test_oracle_connection_error(self):
        """Test Oracle connection error handling."""
        from app.core.oracle.connection import OracleConnectionError

        with patch("app.services.bug_detection_service.BugDetectionService.detect_bugs_for_query") as mock_detect:
            mock_detect.side_effect = OracleConnectionError("Connection failed")

            response = client.get("/api/v1/bugs/abc123def4567")

            assert response.status_code == 502
            data = response.json()
            assert data["detail"]["code"] == "ORACLE_CONNECTION_ERROR"

    def test_sql_id_case_insensitive(self, sample_bugs):
        """Test that SQL_ID is converted to uppercase."""
        detection_result = {
            "sql_id": "ABC123DEF4567",
            "detected_bugs": [],
            "summary": {
                "total_bugs": 0,
                "by_severity": {},
                "by_category": {},
                "high_confidence_count": 0,
                "critical_count": 0,
            },
            "database_version": None,
            "detection_timestamp": "2024-01-15T10:30:00",
        }

        with patch("app.services.bug_detection_service.BugDetectionService.detect_bugs_for_query") as mock_detect:
            mock_detect.return_value = detection_result

            # Pass lowercase SQL_ID
            response = client.get("/api/v1/bugs/abc123def4567")

            assert response.status_code == 200
            # Verify service was called with uppercase
            mock_detect.assert_called_once()
            call_args = mock_detect.call_args
            assert call_args[1]["sql_id"] == "ABC123DEF4567"
