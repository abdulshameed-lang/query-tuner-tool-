"""Oracle connection schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OracleConnectionCreate(BaseModel):
    """Schema for creating Oracle connection."""
    connection_name: str = Field(..., min_length=1, max_length=100)
    host: str = Field(..., min_length=1)
    port: int = Field(default=1521, ge=1, le=65535)
    service_name: Optional[str] = None
    sid: Optional[str] = None
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_default: bool = False


class OracleConnectionUpdate(BaseModel):
    """Schema for updating Oracle connection."""
    connection_name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    service_name: Optional[str] = None
    sid: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class OracleConnectionResponse(BaseModel):
    """Schema for Oracle connection response (without password)."""
    id: int
    connection_name: str
    host: str
    port: int
    service_name: Optional[str]
    sid: Optional[str]
    username: str
    description: Optional[str]
    is_default: bool
    is_active: bool
    created_at: datetime
    last_connected_at: Optional[datetime]

    class Config:
        from_attributes = True


class OracleConnectionTest(BaseModel):
    """Schema for testing Oracle connection."""
    host: str
    port: int = 1521
    service_name: Optional[str] = None
    sid: Optional[str] = None
    username: str
    password: str
