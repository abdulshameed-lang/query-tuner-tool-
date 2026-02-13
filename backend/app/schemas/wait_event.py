"""Pydantic schemas for wait events."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WaitEvent(BaseModel):
    """Individual wait event from ASH or V$SESSION_WAIT."""

    sql_id: Optional[str] = Field(None, description="SQL ID")
    sample_time: Optional[str] = Field(None, description="Sample time")
    session_id: Optional[int] = Field(None, description="Session ID")
    session_serial: Optional[int] = Field(None, description="Session serial number")
    event: Optional[str] = Field(None, description="Wait event name")
    wait_class: Optional[str] = Field(None, description="Wait class")
    wait_time: Optional[int] = Field(None, description="Wait time in centiseconds")
    time_waited: Optional[int] = Field(None, description="Time waited in microseconds")
    p1text: Optional[str] = Field(None, description="Parameter 1 name")
    p1: Optional[int] = Field(None, description="Parameter 1 value")
    p2text: Optional[str] = Field(None, description="Parameter 2 name")
    p2: Optional[int] = Field(None, description="Parameter 2 value")
    p3text: Optional[str] = Field(None, description="Parameter 3 name")
    p3: Optional[int] = Field(None, description="Parameter 3 value")
    current_obj: Optional[int] = Field(None, description="Current object number")
    current_file: Optional[int] = Field(None, description="Current file number")
    current_block: Optional[int] = Field(None, description="Current block number")
    session_state: Optional[str] = Field(None, description="Session state")
    blocking_session: Optional[int] = Field(None, description="Blocking session ID")
    blocking_session_serial: Optional[int] = Field(
        None, description="Blocking session serial"
    )
    sql_plan_hash_value: Optional[int] = Field(None, description="SQL plan hash value")
    sql_plan_line_id: Optional[int] = Field(None, description="SQL plan line ID")
    category: Optional[str] = Field(None, description="Wait event category")

    class Config:
        from_attributes = True


class CurrentWaitEvent(BaseModel):
    """Current wait event from V$SESSION_WAIT."""

    sid: int = Field(..., description="Session ID")
    serial: int = Field(..., description="Session serial number")
    username: Optional[str] = Field(None, description="Username")
    program: Optional[str] = Field(None, description="Program name")
    sql_id: Optional[str] = Field(None, description="SQL ID")
    event: str = Field(..., description="Wait event name")
    wait_class: str = Field(..., description="Wait class")
    state: str = Field(..., description="Wait state")
    wait_time: Optional[int] = Field(None, description="Wait time")
    seconds_in_wait: Optional[int] = Field(None, description="Seconds in wait")
    p1text: Optional[str] = Field(None, description="Parameter 1 name")
    p1: Optional[int] = Field(None, description="Parameter 1 value")
    p2text: Optional[str] = Field(None, description="Parameter 2 name")
    p2: Optional[int] = Field(None, description="Parameter 2 value")
    p3text: Optional[str] = Field(None, description="Parameter 3 name")
    p3: Optional[int] = Field(None, description="Parameter 3 value")
    category: Optional[str] = Field(None, description="Wait event category")

    class Config:
        from_attributes = True


class WaitEventSummary(BaseModel):
    """Aggregated wait event summary."""

    event: str = Field(..., description="Wait event name")
    wait_class: str = Field(..., description="Wait class")
    category: str = Field(..., description="Wait event category")
    wait_count: int = Field(..., description="Number of waits")
    total_time_waited: float = Field(..., description="Total time waited (microseconds)")
    avg_time_waited: Optional[float] = Field(
        None, description="Average time waited (microseconds)"
    )
    max_time_waited: Optional[float] = Field(
        None, description="Maximum time waited (microseconds)"
    )
    percentage: float = Field(..., description="Percentage of total wait time")


class WaitEventCategory(BaseModel):
    """Wait event category aggregation."""

    category: str = Field(..., description="Category key")
    name: str = Field(..., description="Category display name")
    color: str = Field(..., description="Category color")
    total_time_waited: float = Field(..., description="Total time waited")
    wait_count: Optional[int] = Field(None, description="Number of waits")
    event_types: Optional[int] = Field(None, description="Number of event types")
    session_count: Optional[int] = Field(None, description="Number of sessions")
    total_wait_time: Optional[float] = Field(None, description="Total wait time (seconds)")
    percentage: Optional[float] = Field(None, description="Percentage of total time")


class WaitEventTimelineBucket(BaseModel):
    """Time bucket for wait event timeline."""

    sample_minute: str = Field(..., description="Sample time (minute)")
    wait_class: str = Field(..., description="Wait class")
    category: str = Field(..., description="Wait event category")
    sample_count: int = Field(..., description="Number of samples")
    total_time_waited: float = Field(..., description="Total time waited")


class BlockingSession(BaseModel):
    """Blocking session information."""

    blocking_session: int = Field(..., description="Blocking session ID")
    blocking_session_serial: int = Field(..., description="Blocking session serial")
    blocking_username: Optional[str] = Field(None, description="Blocking username")
    blocking_program: Optional[str] = Field(None, description="Blocking program")
    blocking_sql_id: Optional[str] = Field(None, description="Blocking SQL ID")
    event: str = Field(..., description="Wait event")
    block_count: int = Field(..., description="Number of times blocked")


class WaitEventRecommendation(BaseModel):
    """Wait event tuning recommendation."""

    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority (low, medium, high)")
    message: str = Field(..., description="Recommendation message")
    suggestions: List[str] = Field(..., description="List of suggestions")
    blocking_sessions: Optional[List[BlockingSession]] = Field(
        None, description="Related blocking sessions"
    )


class WaitEventsResponse(BaseModel):
    """API response for wait events by SQL_ID."""

    data: Dict[str, Any] = Field(..., description="Wait event data")


class CurrentWaitEventsResponse(BaseModel):
    """API response for current system wait events."""

    data: Dict[str, Any] = Field(..., description="Current wait event data")


class WaitEventSQLBreakdown(BaseModel):
    """Wait events grouped by SQL_ID."""

    sql_id: str = Field(..., description="SQL ID")
    session_count: int = Field(..., description="Number of sessions")
    events: List[str] = Field(..., description="List of wait events")
