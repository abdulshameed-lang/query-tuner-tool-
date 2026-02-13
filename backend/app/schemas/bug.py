"""Pydantic schemas for bug detection."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BugEvidence(BaseModel):
    """Evidence for bug detection."""

    execution_plan: Optional[Dict[str, Any]] = Field(None, description="Plan evidence")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameter evidence")
    query_characteristics: Optional[Dict[str, Any]] = Field(
        None, description="Query characteristic evidence"
    )
    wait_events: Optional[Dict[str, Any]] = Field(None, description="Wait event evidence")
    sql_characteristics: Optional[Dict[str, Any]] = Field(
        None, description="SQL pattern evidence"
    )
    alert_log: Optional[Dict[str, Any]] = Field(None, description="Alert log evidence")

    class Config:
        from_attributes = True


class Bug(BaseModel):
    """Oracle bug information."""

    bug_number: str = Field(..., description="Oracle bug number")
    title: str = Field(..., description="Bug title")
    category: str = Field(..., description="Bug category")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Bug description")
    symptoms: List[str] = Field(..., description="Bug symptoms")
    affected_versions: List[str] = Field(..., description="Affected Oracle versions")
    fixed_versions: List[str] = Field(..., description="Fixed in versions")
    workarounds: List[str] = Field(..., description="Workaround suggestions")
    remediation_sql: Optional[str] = Field(None, description="SQL to remediate")
    my_oracle_support_url: Optional[str] = Field(None, description="MOS doc URL")

    class Config:
        from_attributes = True


class BugMatch(BaseModel):
    """Detected bug match."""

    bug: Bug = Field(..., description="Bug information")
    confidence: int = Field(..., description="Confidence score (0-100)")
    matched_patterns: List[str] = Field(..., description="Matched detection patterns")
    evidence: BugEvidence = Field(..., description="Evidence for detection")
    sql_id: Optional[str] = Field(None, description="Related SQL_ID")

    class Config:
        from_attributes = True


class BugDetectionSummary(BaseModel):
    """Summary of bug detection results."""

    total_bugs: int = Field(..., description="Total bugs detected")
    by_severity: Dict[str, int] = Field(..., description="Count by severity")
    by_category: Dict[str, int] = Field(..., description="Count by category")
    high_confidence_count: int = Field(
        ..., description="Number of high confidence matches"
    )
    critical_count: int = Field(..., description="Number of critical bugs")

    class Config:
        from_attributes = True


class BugDetectionResponse(BaseModel):
    """API response for bug detection."""

    sql_id: Optional[str] = Field(None, description="SQL_ID analyzed")
    detected_bugs: List[BugMatch] = Field(..., description="List of detected bugs")
    summary: BugDetectionSummary = Field(..., description="Detection summary")
    database_version: Optional[str] = Field(None, description="Database version")
    detection_timestamp: str = Field(..., description="When detection was performed")


class BugListResponse(BaseModel):
    """API response for bug list."""

    bugs: List[Bug] = Field(..., description="List of bugs")
    total_count: int = Field(..., description="Total number of bugs")
    filters_applied: Optional[Dict[str, Any]] = Field(
        None, description="Applied filters"
    )


class AlertLogBugResponse(BaseModel):
    """API response for alert log bug detection."""

    detected_bugs: List[BugMatch] = Field(..., description="Bugs detected from alert log")
    total_count: int = Field(..., description="Total bugs detected")
    summary: BugDetectionSummary = Field(..., description="Detection summary")


class VersionCheckResponse(BaseModel):
    """API response for version-specific bug check."""

    database_version: str = Field(..., description="Database version checked")
    bugs_affecting_version: List[Bug] = Field(
        ..., description="Bugs affecting this version"
    )
    total_count: int = Field(..., description="Total bugs found")
    critical_count: int = Field(..., description="Critical bugs count")
    recommendation: str = Field(..., description="Overall recommendation")
