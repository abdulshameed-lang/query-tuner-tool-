"""Oracle bug detection engine.

This module analyzes SQL queries, execution plans, and system state
to detect known Oracle bugs.
"""

from typing import List, Dict, Any, Optional
import logging
import re

from app.core.oracle.bug_patterns import BugPatternDatabase, BugSeverity, BugCategory

logger = logging.getLogger(__name__)


class BugDetector:
    """Detects known Oracle bugs based on various signals."""

    def __init__(self):
        """Initialize BugDetector."""
        self.bug_db = BugPatternDatabase()

    def detect_bugs(
        self,
        sql_id: Optional[str] = None,
        sql_text: Optional[str] = None,
        plan_operations: Optional[List[Dict[str, Any]]] = None,
        query_metrics: Optional[Dict[str, Any]] = None,
        database_version: Optional[str] = None,
        init_parameters: Optional[Dict[str, str]] = None,
        wait_events: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect potential bugs based on provided information.

        Args:
            sql_id: SQL_ID to analyze
            sql_text: SQL query text
            plan_operations: Execution plan operations
            query_metrics: Query performance metrics
            database_version: Oracle database version
            init_parameters: Database initialization parameters
            wait_events: List of wait events

        Returns:
            List of detected bug matches with confidence scores
        """
        detected_bugs = []

        # Get all bugs from database
        all_bugs = self.bug_db.get_all_bugs()

        # Filter by database version if provided
        if database_version:
            all_bugs = [
                bug for bug in all_bugs
                if self.bug_db._version_affected(
                    database_version,
                    bug.get("affected_versions", [])
                )
            ]

        # Analyze each bug pattern
        for bug in all_bugs:
            match = self._analyze_bug_pattern(
                bug=bug,
                sql_text=sql_text,
                plan_operations=plan_operations,
                query_metrics=query_metrics,
                init_parameters=init_parameters,
                wait_events=wait_events,
            )

            if match:
                # Add match with confidence score
                detected_bugs.append({
                    "bug": bug,
                    "confidence": match["confidence"],
                    "matched_patterns": match["matched_patterns"],
                    "evidence": match["evidence"],
                    "sql_id": sql_id,
                })

        # Sort by confidence (highest first)
        detected_bugs.sort(key=lambda x: x["confidence"], reverse=True)

        logger.info(f"Detected {len(detected_bugs)} potential bug matches")

        return detected_bugs

    def detect_bugs_from_alert_log(
        self, alert_log_entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect bugs from alert log entries.

        Args:
            alert_log_entries: List of alert log entries with errors

        Returns:
            List of detected bugs
        """
        detected_bugs = []

        for entry in alert_log_entries:
            error_code = entry.get("error_code")
            error_message = entry.get("message", "")

            if error_code:
                # Find bugs associated with this error
                matching_bugs = self.bug_db.get_bugs_by_alert_error(error_code)

                for bug in matching_bugs:
                    # Check if error message matches bug keywords
                    detection_patterns = bug.get("detection_patterns", {})
                    alert_patterns = detection_patterns.get("alert_log", {})
                    keywords = alert_patterns.get("keywords", [])

                    confidence = 50  # Base confidence for error match

                    # Increase confidence if keywords match
                    matched_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in error_message.lower():
                            confidence += 10
                            matched_keywords.append(keyword)

                    detected_bugs.append({
                        "bug": bug,
                        "confidence": min(confidence, 100),
                        "matched_patterns": ["alert_log_error"],
                        "evidence": {
                            "error_code": error_code,
                            "error_message": error_message,
                            "matched_keywords": matched_keywords,
                            "timestamp": entry.get("timestamp"),
                        },
                    })

        return detected_bugs

    def _analyze_bug_pattern(
        self,
        bug: Dict[str, Any],
        sql_text: Optional[str],
        plan_operations: Optional[List[Dict[str, Any]]],
        query_metrics: Optional[Dict[str, Any]],
        init_parameters: Optional[Dict[str, str]],
        wait_events: Optional[List[Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze if a specific bug pattern matches current conditions.

        Args:
            bug: Bug pattern to check
            sql_text: SQL query text
            plan_operations: Execution plan operations
            query_metrics: Query metrics
            init_parameters: Database parameters
            wait_events: Wait events

        Returns:
            Match information with confidence score, or None if no match
        """
        detection_patterns = bug.get("detection_patterns", {})
        matched_patterns = []
        evidence = {}
        confidence = 0

        # Check execution plan patterns
        if plan_operations and "execution_plan" in detection_patterns:
            plan_match = self._check_plan_pattern(
                plan_operations,
                detection_patterns["execution_plan"]
            )
            if plan_match:
                matched_patterns.append("execution_plan")
                evidence["execution_plan"] = plan_match
                confidence += 30

        # Check parameter patterns
        if init_parameters and "parameters" in detection_patterns:
            param_match = self._check_parameter_pattern(
                init_parameters,
                detection_patterns["parameters"]
            )
            if param_match:
                matched_patterns.append("parameters")
                evidence["parameters"] = param_match
                confidence += 25

        # Check query characteristics
        if query_metrics and "query_characteristics" in detection_patterns:
            query_match = self._check_query_characteristics(
                query_metrics,
                detection_patterns["query_characteristics"]
            )
            if query_match:
                matched_patterns.append("query_characteristics")
                evidence["query_characteristics"] = query_match
                confidence += 20

        # Check wait events
        if wait_events and "wait_events" in detection_patterns:
            wait_match = self._check_wait_events(
                wait_events,
                detection_patterns["wait_events"]
            )
            if wait_match:
                matched_patterns.append("wait_events")
                evidence["wait_events"] = wait_match
                confidence += 25

        # Check SQL characteristics
        if sql_text and "sql_characteristics" in detection_patterns:
            sql_match = self._check_sql_pattern(
                sql_text,
                detection_patterns["sql_characteristics"]
            )
            if sql_match:
                matched_patterns.append("sql_characteristics")
                evidence["sql_characteristics"] = sql_match
                confidence += 20

        # Return match if confidence threshold met
        if confidence >= 50:  # Require at least 50% confidence
            return {
                "confidence": min(confidence, 100),
                "matched_patterns": matched_patterns,
                "evidence": evidence,
            }

        return None

    def _check_plan_pattern(
        self,
        plan_operations: List[Dict[str, Any]],
        pattern: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if execution plan matches pattern."""
        evidence = {}

        # Check for specific operations
        if "operations" in pattern:
            required_ops = pattern["operations"]
            found_ops = []

            for op in plan_operations:
                operation = op.get("operation", "")
                options = op.get("options", "")
                full_op = f"{operation} {options}".strip()

                for required in required_ops:
                    if required.upper() in full_op.upper():
                        found_ops.append(full_op)

            if found_ops:
                evidence["operations_found"] = found_ops

        # Check cardinality mismatch
        if "cardinality_mismatch_ratio" in pattern:
            threshold_str = pattern["cardinality_mismatch_ratio"]
            threshold = float(threshold_str.replace(">", "").replace("<", ""))

            for op in plan_operations:
                estimated = op.get("cardinality", 0)
                # In reality, would compare with actual rows
                # For now, just check if cardinality exists
                if estimated > 0:
                    evidence["cardinality_check"] = "present"

        # Check cost threshold
        if "cost" in pattern:
            cost_pattern = pattern["cost"]
            threshold = int(cost_pattern.replace(">", "").replace("<", ""))

            for op in plan_operations:
                cost = op.get("cost", 0)
                if cost > threshold:
                    evidence["high_cost_operation"] = {
                        "operation": op.get("operation"),
                        "cost": cost
                    }

        return evidence if evidence else None

    def _check_parameter_pattern(
        self,
        init_parameters: Dict[str, str],
        pattern: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Check if database parameters match pattern."""
        evidence = {}

        for param_name, expected_value in pattern.items():
            actual_value = init_parameters.get(param_name)

            if actual_value:
                # Simple string match for now
                if expected_value.lower() in str(actual_value).lower():
                    evidence[param_name] = {
                        "expected": expected_value,
                        "actual": actual_value,
                    }

        return evidence if evidence else None

    def _check_query_characteristics(
        self,
        query_metrics: Dict[str, Any],
        pattern: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if query characteristics match pattern."""
        evidence = {}

        # Check version count
        if "version_count" in pattern:
            threshold_str = pattern["version_count"]
            threshold = int(threshold_str.replace(">", "").replace("<", ""))
            actual = query_metrics.get("version_count", 0)

            if ">" in threshold_str and actual > threshold:
                evidence["version_count"] = actual
            elif "<" in threshold_str and actual < threshold:
                evidence["version_count"] = actual

        # Check parse calls
        if "parse_calls" in pattern:
            threshold_str = pattern["parse_calls"]
            threshold = int(threshold_str.replace(">", "").replace("<", ""))
            actual = query_metrics.get("parse_calls", 0)

            if ">" in threshold_str and actual > threshold:
                evidence["parse_calls"] = actual

        # Check buffer gets
        if "buffer_gets" in pattern:
            threshold_str = pattern["buffer_gets"]
            threshold = int(threshold_str.replace(">", "").replace("<", ""))
            actual = query_metrics.get("buffer_gets", 0)

            if ">" in threshold_str and actual > threshold:
                evidence["buffer_gets"] = actual

        # Check bind variables
        if "bind_variables" in pattern:
            if query_metrics.get("bind_variables"):
                evidence["bind_variables"] = True

        # Check partitioned table
        if "partitioned_table" in pattern:
            if query_metrics.get("partitioned_table"):
                evidence["partitioned_table"] = True

        return evidence if evidence else None

    def _check_wait_events(
        self,
        wait_events: List[Dict[str, Any]],
        pattern: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if wait events match pattern."""
        evidence = {}

        event_name_pattern = pattern.get("event_name")
        wait_time_pattern = pattern.get("wait_time")

        for event in wait_events:
            event_name = event.get("event_name", "")

            # Check event name match
            if event_name_pattern and event_name_pattern.lower() in event_name.lower():
                # Check wait time threshold if specified
                if wait_time_pattern:
                    threshold = int(wait_time_pattern.replace(">", "").replace("<", ""))
                    wait_time = event.get("wait_time", 0)

                    if ">" in wait_time_pattern and wait_time > threshold:
                        evidence["wait_event"] = {
                            "name": event_name,
                            "wait_time": wait_time
                        }
                else:
                    evidence["wait_event"] = {"name": event_name}

        return evidence if evidence else None

    def _check_sql_pattern(
        self,
        sql_text: str,
        pattern: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if SQL text matches pattern."""
        evidence = {}

        # Check for specific SQL patterns
        if "keywords" in pattern:
            keywords = pattern["keywords"]
            sql_upper = sql_text.upper()

            found_keywords = []
            for keyword in keywords:
                if keyword.upper() in sql_upper:
                    found_keywords.append(keyword)

            if found_keywords:
                evidence["keywords_found"] = found_keywords

        return evidence if evidence else None

    def get_bug_remediation(
        self, bug_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get remediation information for a specific bug.

        Args:
            bug_number: Oracle bug number

        Returns:
            Remediation information
        """
        bug = self.bug_db.get_bug_by_number(bug_number)

        if not bug:
            return None

        return {
            "bug_number": bug["bug_number"],
            "title": bug["title"],
            "severity": bug["severity"],
            "workarounds": bug.get("workarounds", []),
            "remediation_sql": bug.get("remediation_sql"),
            "patch_available": len(bug.get("fixed_versions", [])) > 0,
            "fixed_versions": bug.get("fixed_versions", []),
            "my_oracle_support_url": bug.get("my_oracle_support_url"),
        }

    def get_detection_summary(
        self, detected_bugs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary of detected bugs.

        Args:
            detected_bugs: List of detected bugs

        Returns:
            Summary statistics
        """
        if not detected_bugs:
            return {
                "total_bugs": 0,
                "by_severity": {},
                "by_category": {},
                "high_confidence_count": 0,
            }

        by_severity = {}
        by_category = {}
        high_confidence = 0

        for detection in detected_bugs:
            bug = detection["bug"]
            confidence = detection["confidence"]

            # Count by severity
            severity = bug["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # Count by category
            category = bug["category"]
            by_category[category] = by_category.get(category, 0) + 1

            # Count high confidence
            if confidence >= 75:
                high_confidence += 1

        return {
            "total_bugs": len(detected_bugs),
            "by_severity": by_severity,
            "by_category": by_category,
            "high_confidence_count": high_confidence,
            "critical_count": by_severity.get(BugSeverity.CRITICAL, 0),
        }
