"""Database models for user accounts and Oracle connections."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    oracle_connections = relationship("OracleConnection", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class OracleConnection(Base):
    """Oracle database connection configuration."""

    __tablename__ = "oracle_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_name = Column(String(100), nullable=False)  # User-friendly name
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=1521, nullable=False)
    service_name = Column(String(100))
    sid = Column(String(100))
    username = Column(String(100), nullable=False)
    encrypted_password = Column(Text, nullable=False)  # Encrypted password
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_connected_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="oracle_connections")

    def __repr__(self):
        return f"<OracleConnection(id={self.id}, name='{self.connection_name}', host='{self.host}')>"

    @property
    def dsn(self):
        """Get DSN string for Oracle connection."""
        if self.service_name:
            return f"{self.host}:{self.port}/{self.service_name}"
        elif self.sid:
            return f"{self.host}:{self.port}/{self.sid}"
        return None
