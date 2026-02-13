"""Oracle connection management service."""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import oracledb

from app.db.models import User, OracleConnection
from app.schemas.oracle_connection import (
    OracleConnectionCreate,
    OracleConnectionUpdate,
    OracleConnectionTest
)
from app.core.security import encrypt_password, decrypt_password


class OracleConnectionService:
    """Service for managing Oracle database connections."""

    @staticmethod
    def create_connection(
        db: Session,
        user: User,
        connection_create: OracleConnectionCreate
    ) -> OracleConnection:
        """Create a new Oracle connection for user."""
        # Validate that service_name or sid is provided
        if not connection_create.service_name and not connection_create.sid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either service_name or sid must be provided"
            )

        # If this is default, unset other defaults
        if connection_create.is_default:
            db.query(OracleConnection).filter(
                OracleConnection.user_id == user.id,
                OracleConnection.is_default == True
            ).update({"is_default": False})

        # Encrypt password
        encrypted_password = encrypt_password(connection_create.password)

        # Create connection
        db_connection = OracleConnection(
            user_id=user.id,
            connection_name=connection_create.connection_name,
            host=connection_create.host,
            port=connection_create.port,
            service_name=connection_create.service_name,
            sid=connection_create.sid,
            username=connection_create.username,
            encrypted_password=encrypted_password,
            description=connection_create.description,
            is_default=connection_create.is_default
        )

        db.add(db_connection)
        db.commit()
        db.refresh(db_connection)

        return db_connection

    @staticmethod
    def get_user_connections(db: Session, user: User) -> List[OracleConnection]:
        """Get all Oracle connections for user."""
        return db.query(OracleConnection).filter(
            OracleConnection.user_id == user.id
        ).order_by(OracleConnection.is_default.desc(), OracleConnection.connection_name).all()

    @staticmethod
    def get_connection(db: Session, user: User, connection_id: int) -> Optional[OracleConnection]:
        """Get a specific Oracle connection for user."""
        return db.query(OracleConnection).filter(
            OracleConnection.id == connection_id,
            OracleConnection.user_id == user.id
        ).first()

    @staticmethod
    def get_default_connection(db: Session, user: User) -> Optional[OracleConnection]:
        """Get user's default Oracle connection."""
        return db.query(OracleConnection).filter(
            OracleConnection.user_id == user.id,
            OracleConnection.is_default == True,
            OracleConnection.is_active == True
        ).first()

    @staticmethod
    def update_connection(
        db: Session,
        user: User,
        connection_id: int,
        connection_update: OracleConnectionUpdate
    ) -> OracleConnection:
        """Update an Oracle connection."""
        db_connection = OracleConnectionService.get_connection(db, user, connection_id)

        if not db_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )

        # Update fields
        update_data = connection_update.dict(exclude_unset=True)

        # Handle password encryption
        if "password" in update_data:
            update_data["encrypted_password"] = encrypt_password(update_data.pop("password"))

        # Handle default flag
        if update_data.get("is_default") is True:
            db.query(OracleConnection).filter(
                OracleConnection.user_id == user.id,
                OracleConnection.id != connection_id,
                OracleConnection.is_default == True
            ).update({"is_default": False})

        for key, value in update_data.items():
            setattr(db_connection, key, value)

        db.commit()
        db.refresh(db_connection)

        return db_connection

    @staticmethod
    def delete_connection(db: Session, user: User, connection_id: int) -> None:
        """Delete an Oracle connection."""
        db_connection = OracleConnectionService.get_connection(db, user, connection_id)

        if not db_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )

        db.delete(db_connection)
        db.commit()

    @staticmethod
    def test_connection(connection_test: OracleConnectionTest) -> dict:
        """Test Oracle connection."""
        try:
            # Build DSN
            if connection_test.service_name:
                dsn = f"{connection_test.host}:{connection_test.port}/{connection_test.service_name}"
            elif connection_test.sid:
                dsn = f"{connection_test.host}:{connection_test.port}/{connection_test.sid}"
            else:
                return {
                    "success": False,
                    "message": "Either service_name or sid must be provided"
                }

            # Attempt connection
            connection = oracledb.connect(
                user=connection_test.username,
                password=connection_test.password,
                dsn=dsn
            )

            # Get database version
            cursor = connection.cursor()
            cursor.execute("SELECT banner FROM v$version WHERE rownum = 1")
            version = cursor.fetchone()[0]
            cursor.close()
            connection.close()

            return {
                "success": True,
                "message": "Connection successful",
                "version": version
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }

    @staticmethod
    def update_last_connected(db: Session, connection_id: int) -> None:
        """Update last connected timestamp."""
        db.query(OracleConnection).filter(
            OracleConnection.id == connection_id
        ).update({"last_connected_at": datetime.utcnow()})
        db.commit()
