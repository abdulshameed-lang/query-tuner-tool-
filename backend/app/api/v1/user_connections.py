"""Oracle connection management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.core.deps import get_current_user
from app.schemas.oracle_connection import (
    OracleConnectionCreate,
    OracleConnectionUpdate,
    OracleConnectionResponse,
    OracleConnectionTest
)
from app.services.oracle_connection_service import OracleConnectionService

router = APIRouter()


@router.post("/", response_model=OracleConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_connection(
    connection_create: OracleConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new Oracle database connection.

    The password will be encrypted before storage.
    """
    connection = OracleConnectionService.create_connection(db, current_user, connection_create)
    return OracleConnectionResponse.from_orm(connection)


@router.get("/", response_model=List[OracleConnectionResponse])
def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all Oracle connections for current user.
    """
    connections = OracleConnectionService.get_user_connections(db, current_user)
    return [OracleConnectionResponse.from_orm(conn) for conn in connections]


@router.get("/default", response_model=OracleConnectionResponse)
def get_default_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the default Oracle connection for current user.
    """
    connection = OracleConnectionService.get_default_connection(db, current_user)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default connection found"
        )
    return OracleConnectionResponse.from_orm(connection)


@router.get("/{connection_id}", response_model=OracleConnectionResponse)
def get_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific Oracle connection.
    """
    connection = OracleConnectionService.get_connection(db, current_user, connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    return OracleConnectionResponse.from_orm(connection)


@router.put("/{connection_id}", response_model=OracleConnectionResponse)
def update_connection(
    connection_id: int,
    connection_update: OracleConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an Oracle connection.
    """
    connection = OracleConnectionService.update_connection(
        db, current_user, connection_id, connection_update
    )
    return OracleConnectionResponse.from_orm(connection)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an Oracle connection.
    """
    OracleConnectionService.delete_connection(db, current_user, connection_id)
    return None


@router.post("/test", response_model=dict)
def test_connection(connection_test: OracleConnectionTest):
    """
    Test an Oracle connection without saving it.

    Returns success status and Oracle version if successful.
    """
    result = OracleConnectionService.test_connection(connection_test)
    return result
