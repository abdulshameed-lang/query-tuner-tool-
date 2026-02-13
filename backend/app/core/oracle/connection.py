"""Oracle database connection management with connection pooling."""

from typing import Optional, TYPE_CHECKING, Any
import logging
from contextlib import contextmanager

from app.config import settings

# Optional Oracle import - don't crash if not available
try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    cx_Oracle = None
    ORACLE_AVAILABLE = False

# Type checking imports (not evaluated at runtime)
if TYPE_CHECKING and cx_Oracle:
    from cx_Oracle import SessionPool, Connection
else:
    SessionPool = Any
    Connection = Any

logger = logging.getLogger(__name__)


class OracleConnectionError(Exception):
    """Raised when Oracle connection fails."""

    def __init__(self, message: str, code: str = "ORACLE_CONNECTION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConnectionManager:
    """Manages Oracle database connections with connection pooling."""

    def __init__(
        self,
        user: str,
        password: str,
        dsn: str,
        min_pool_size: int = 5,
        max_pool_size: int = 20,
    ):
        """
        Initialize connection manager.

        Args:
            user: Oracle database username
            password: Oracle database password
            dsn: Oracle database DSN (host:port/service_name)
            min_pool_size: Minimum connections in pool
            max_pool_size: Maximum connections in pool
        """
        if not ORACLE_AVAILABLE:
            raise OracleConnectionError("cx_Oracle not available - cannot create connection manager")

        self.user = user
        self.password = password
        self.dsn = dsn
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._pool: Optional[SessionPool] = None

    def create_pool(self) -> SessionPool:
        """
        Create Oracle connection pool.

        Returns:
            Oracle session pool

        Raises:
            OracleConnectionError: If pool creation fails
        """
        try:
            logger.info(
                f"Creating Oracle connection pool: "
                f"DSN={self.dsn}, min={self.min_pool_size}, max={self.max_pool_size}"
            )

            self._pool = cx_Oracle.SessionPool(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                min=self.min_pool_size,
                max=self.max_pool_size,
                increment=1,
                threaded=True,
                getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT,
                timeout=300,  # Connection timeout (seconds)
                wait_timeout=10000,  # Wait timeout for connection (ms)
                max_lifetime_session=3600,  # Max session lifetime (seconds)
            )

            logger.info("Oracle connection pool created successfully")
            return self._pool

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            error_message = f"Failed to create connection pool: {error.message}"
            logger.error(error_message)
            raise OracleConnectionError(error_message) from e

    def get_pool(self) -> cx_Oracle.SessionPool:
        """
        Get existing connection pool or create new one.

        Returns:
            Oracle session pool

        Raises:
            OracleConnectionError: If pool doesn't exist and creation fails
        """
        if self._pool is None:
            return self.create_pool()
        return self._pool

    @contextmanager
    def get_connection(self):
        """
        Context manager for acquiring and releasing connections.

        Yields:
            Oracle connection from pool

        Raises:
            OracleConnectionError: If connection acquisition fails

        Example:
            with manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM v$version")
        """
        connection = None
        try:
            pool = self.get_pool()
            connection = pool.acquire()
            yield connection
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            logger.error(f"Database error: {error.message}")
            if connection:
                connection.rollback()
            raise OracleConnectionError(f"Database error: {error.message}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                pool = self.get_pool()
                pool.release(connection)

    def test_connection(self) -> dict:
        """
        Test Oracle database connection.

        Returns:
            Dictionary with connection test results

        Raises:
            OracleConnectionError: If connection test fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get Oracle version
                cursor.execute("SELECT banner FROM v$version WHERE rownum = 1")
                version_row = cursor.fetchone()
                version = version_row[0] if version_row else "Unknown"

                # Get database name
                cursor.execute("SELECT name FROM v$database")
                db_name_row = cursor.fetchone()
                db_name = db_name_row[0] if db_name_row else "Unknown"

                # Get current user
                cursor.execute("SELECT user FROM dual")
                user_row = cursor.fetchone()
                current_user = user_row[0] if user_row else "Unknown"

                cursor.close()

                logger.info(f"Connection test successful: {db_name} ({version})")

                return {
                    "status": "connected",
                    "version": version,
                    "database": db_name,
                    "user": current_user,
                    "dsn": self.dsn,
                }

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            error_message = f"Connection test failed: {error.message}"
            logger.error(error_message)
            raise OracleConnectionError(error_message) from e

    def close_pool(self):
        """Close connection pool and release all connections."""
        if self._pool:
            try:
                logger.info("Closing Oracle connection pool")
                self._pool.close()
                self._pool = None
                logger.info("Oracle connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")

    def get_pool_stats(self) -> dict:
        """
        Get connection pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        if not self._pool:
            return {"status": "not_initialized"}

        return {
            "status": "active",
            "min_size": self._pool.min,
            "max_size": self._pool.max,
            "busy_count": self._pool.busy,
            "open_count": self._pool.opened,
            "timeout": self._pool.timeout,
        }


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get global connection manager instance.

    Returns:
        ConnectionManager instance

    Raises:
        OracleConnectionError: If connection manager is not initialized
    """
    global _connection_manager

    if _connection_manager is None:
        # Initialize from settings
        if not settings.oracle_user or not settings.oracle_password or not settings.oracle_dsn:
            raise OracleConnectionError(
                "Oracle connection not configured. Set ORACLE_USER, ORACLE_PASSWORD, and ORACLE_DSN environment variables."
            )

        _connection_manager = ConnectionManager(
            user=settings.oracle_user,
            password=settings.oracle_password,
            dsn=settings.oracle_dsn,
            min_pool_size=settings.oracle_min_pool_size,
            max_pool_size=settings.oracle_max_pool_size,
        )

    return _connection_manager


def close_connection_manager():
    """Close global connection manager."""
    global _connection_manager
    if _connection_manager:
        _connection_manager.close_pool()
        _connection_manager = None
