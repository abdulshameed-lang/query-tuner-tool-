# Error Handling Standards

## Overview

This document defines error handling patterns, exception hierarchies, and best practices for the Oracle Database Performance Tuning Tool.

## Error Handling Principles

### Fail Fast
- Detect errors early
- Don't let bad data propagate
- Validate inputs immediately

### Fail Gracefully
- Provide meaningful error messages
- Don't crash the application
- Allow recovery when possible

### Be Specific
- Use specific exception types
- Provide context in error messages
- Include relevant details for debugging

### Be Consistent
- Consistent error response formats
- Consistent exception handling patterns
- Consistent logging approach

## Python Error Handling

### Exception Hierarchy

Create a clear exception hierarchy:

```python
# Base exception
class QueryTunerError(Exception):
    """Base exception for Query Tuner Tool."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

# Database exceptions
class DatabaseError(QueryTunerError):
    """Base exception for database-related errors."""
    pass

class OracleConnectionError(DatabaseError):
    """Raised when Oracle connection fails."""

    def __init__(self, message: str, host: str = None, port: int = None):
        self.host = host
        self.port = port
        super().__init__(message, code="ORACLE_CONNECTION_ERROR")

class QueryExecutionError(DatabaseError):
    """Raised when query execution fails."""

    def __init__(self, message: str, sql_id: str = None, oracle_error: str = None):
        self.sql_id = sql_id
        self.oracle_error = oracle_error
        super().__init__(message, code="QUERY_EXECUTION_ERROR")

# Validation exceptions
class ValidationError(QueryTunerError):
    """Base exception for validation errors."""
    pass

class InvalidSqlIdError(ValidationError):
    """Raised when SQL_ID format is invalid."""

    def __init__(self, sql_id: str, reason: str):
        self.sql_id = sql_id
        self.reason = reason
        message = f"Invalid SQL_ID '{sql_id}': {reason}"
        super().__init__(message, code="INVALID_SQL_ID")

# Business logic exceptions
class QueryNotFoundError(QueryTunerError):
    """Raised when query is not found."""

    def __init__(self, sql_id: str):
        self.sql_id = sql_id
        message = f"Query with SQL_ID '{sql_id}' not found"
        super().__init__(message, code="QUERY_NOT_FOUND")
```

### Exception Handling Patterns

#### Try-Except Blocks

```python
# Good - Specific exceptions
try:
    connection = pool.acquire()
    result = execute_query(connection, sql, params)
except cx_Oracle.DatabaseError as e:
    error, = e.args
    logger.error(f"Database error: {error.code} - {error.message}")
    raise QueryExecutionError(
        f"Failed to execute query: {error.message}",
        sql_id=sql_id,
        oracle_error=f"ORA-{error.code:05d}"
    ) from e
except cx_Oracle.InterfaceError as e:
    logger.error(f"Connection error: {e}")
    raise OracleConnectionError("Database connection lost") from e
finally:
    if connection:
        pool.release(connection)

# Bad - Catching everything
try:
    do_something()
except Exception:
    pass  # Silently swallowing errors!

# Bad - Too broad
try:
    do_something()
except Exception as e:
    logger.error(f"Error: {e}")
    # What error? Can't handle specifically
```

#### Context Managers

```python
from contextlib import contextmanager

@contextmanager
def get_connection(pool):
    """Context manager for database connections."""
    connection = None
    try:
        connection = pool.acquire()
        yield connection
    except cx_Oracle.DatabaseError as e:
        if connection:
            connection.rollback()
        logger.error(f"Database error: {e}")
        raise DatabaseError(str(e)) from e
    finally:
        if connection:
            pool.release(connection)

# Usage
try:
    with get_connection(pool) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
except DatabaseError as e:
    logger.error(f"Query failed: {e}")
    raise
```

#### Retrying with Exponential Backoff

```python
import time
from typing import TypeVar, Callable

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> T:
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)

# Usage
try:
    result = retry_with_backoff(
        lambda: fetch_queries(connection),
        max_retries=3,
        exceptions=(OracleConnectionError, QueryExecutionError)
    )
except QueryTunerError as e:
    logger.error(f"All retries failed: {e}")
    raise
```

### Input Validation

#### Validate Early

```python
from typing import Optional
import re

def validate_sql_id(sql_id: str) -> str:
    """Validate and normalize SQL_ID format."""
    if not sql_id:
        raise InvalidSqlIdError(sql_id, "SQL_ID cannot be empty")

    if len(sql_id) != 13:
        raise InvalidSqlIdError(
            sql_id,
            f"SQL_ID must be 13 characters, got {len(sql_id)}"
        )

    if not sql_id.isalnum():
        raise InvalidSqlIdError(sql_id, "SQL_ID must be alphanumeric")

    return sql_id.upper()

def get_query_details(sql_id: str) -> Query:
    """Get query details by SQL_ID."""
    # Validate immediately
    try:
        sql_id = validate_sql_id(sql_id)
    except InvalidSqlIdError as e:
        logger.warning(f"Invalid SQL_ID provided: {e}")
        raise

    # Proceed with validated input
    query = fetch_query(sql_id)
    if not query:
        raise QueryNotFoundError(sql_id)

    return query
```

#### Pydantic Validation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class ConnectionRequest(BaseModel):
    """Request model for creating Oracle connection."""
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    service_name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1)

    @validator('host')
    def validate_host(cls, v):
        """Validate host format."""
        if v in ['localhost', '127.0.0.1']:
            raise ValueError('Localhost connections not allowed')
        return v

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v.upper()

# FastAPI endpoint
@router.post("/api/v1/connections")
async def create_connection(request: ConnectionRequest):
    """Create new Oracle connection."""
    try:
        connection = connect_to_oracle(
            host=request.host,
            port=request.port,
            service_name=request.service_name,
            username=request.username,
            password=request.password
        )
        return {"status": "connected", "connectionId": connection.id}
    except OracleConnectionError as e:
        raise HTTPException(
            status_code=502,
            detail={
                "code": e.code,
                "message": e.message,
                "host": e.host,
                "port": e.port
            }
        )
```

### Logging Errors

#### Structured Logging

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Logger with structured output."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def error(self, message: str, **kwargs):
        """Log error with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": message,
            **kwargs
        }
        self.logger.error(json.dumps(log_data))

    def warning(self, message: str, **kwargs):
        """Log warning with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "WARNING",
            "message": message,
            **kwargs
        }
        self.logger.warning(json.dumps(log_data))

# Usage
logger = StructuredLogger(__name__)

try:
    result = fetch_queries(sql_id)
except QueryExecutionError as e:
    logger.error(
        "Query execution failed",
        sql_id=e.sql_id,
        error_code=e.code,
        oracle_error=e.oracle_error,
        user_id=current_user.id
    )
    raise
```

## FastAPI Error Handling

### Custom Exception Handlers

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

# Handle custom exceptions
@app.exception_handler(QueryTunerError)
async def query_tuner_error_handler(request: Request, exc: QueryTunerError):
    """Handle Query Tuner exceptions."""
    status_code = get_status_code(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url),
                "requestId": request.state.request_id
            }
        }
    )

# Handle validation errors
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors},
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url)
            }
        }
    )

# Handle unexpected errors
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't leak details in production
    if settings.environment == "production":
        message = "Internal server error"
    else:
        message = str(exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url),
                "requestId": request.state.request_id
            }
        }
    )

def get_status_code(exc: QueryTunerError) -> int:
    """Map exception to HTTP status code."""
    status_map = {
        QueryNotFoundError: 404,
        InvalidSqlIdError: 400,
        ValidationError: 400,
        OracleConnectionError: 502,
        QueryExecutionError: 500,
    }
    return status_map.get(type(exc), 500)
```

### Dependency Error Handling

```python
from fastapi import Depends, HTTPException

def get_connection_pool():
    """Dependency for connection pool."""
    if not connection_pool:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Database connection pool not initialized"
            }
        )
    return connection_pool

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency for current user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail={"code": "INVALID_TOKEN", "message": "Invalid token"}
            )
        return get_user(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"code": "TOKEN_EXPIRED", "message": "Token expired"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Invalid token"}
        )
```

## TypeScript/React Error Handling

### Error Boundaries

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Log to error reporting service
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Usage
<ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</ErrorBoundary>
```

### API Error Handling

```typescript
// Custom error classes
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

// API client with error handling
export async function fetchQueries(connectionId: string): Promise<Query[]> {
  try {
    const response = await fetch(`/api/v1/queries?connectionId=${connectionId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(
        error.error.code,
        error.error.message,
        response.status,
        error.error.details
      );
    }

    const data = await response.json();
    return data.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof TypeError) {
      throw new NetworkError('Network request failed');
    }

    throw new Error(`Unknown error: ${error}`);
  }
}
```

### React Query Error Handling

```typescript
import { useQuery } from '@tanstack/react-query';

export function useQueries(connectionId: string) {
  return useQuery({
    queryKey: ['queries', connectionId],
    queryFn: () => fetchQueries(connectionId),
    retry: (failureCount, error) => {
      // Don't retry on client errors (4xx)
      if (error instanceof ApiError && error.statusCode >= 400 && error.statusCode < 500) {
        return false;
      }
      // Retry up to 3 times for server errors (5xx)
      return failureCount < 3;
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        if (error.statusCode === 401) {
          // Redirect to login
          window.location.href = '/login';
        } else {
          // Show error notification
          showNotification('error', error.message);
        }
      }
    },
  });
}

// Component using the hook
export const QueriesPage: React.FC = () => {
  const { data, error, isLoading } = useQueries('conn-123');

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return <ErrorDisplay error={error as Error} />;
  }

  return <QueryList queries={data} />;
};
```

### Form Validation

```typescript
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

// Validation schema
const connectionSchema = z.object({
  host: z.string().min(1, 'Host is required').max(255),
  port: z.number().min(1).max(65535),
  serviceName: z.string().min(1, 'Service name is required'),
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type ConnectionFormData = z.infer<typeof connectionSchema>;

export const ConnectionForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ConnectionFormData>({
    resolver: zodResolver(connectionSchema),
  });

  const onSubmit = async (data: ConnectionFormData) => {
    try {
      await createConnection(data);
      showNotification('success', 'Connected successfully');
    } catch (error) {
      if (error instanceof ApiError) {
        showNotification('error', error.message);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('host')} />
      {errors.host && <span className="error">{errors.host.message}</span>}

      <input type="number" {...register('port', { valueAsNumber: true })} />
      {errors.port && <span className="error">{errors.port.message}</span>}

      <button type="submit">Connect</button>
    </form>
  );
};
```

## Error Response Formats

### Success Response

```json
{
  "data": {
    "sqlId": "abc123",
    "sqlText": "SELECT * FROM users",
    "elapsedTime": 1234.56
  },
  "meta": {
    "timestamp": "2024-02-11T13:00:00Z",
    "requestId": "req-12345"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "QUERY_NOT_FOUND",
    "message": "Query with SQL_ID 'abc123' not found",
    "details": {
      "sqlId": "abc123",
      "possibleReasons": [
        "Query may have aged out of V$SQL",
        "SQL_ID may be incorrect"
      ]
    },
    "timestamp": "2024-02-11T13:00:00Z",
    "path": "/api/v1/queries/abc123",
    "requestId": "req-12345"
  }
}
```

### Validation Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "field": "port",
          "message": "Port must be between 1 and 65535",
          "type": "value_error"
        },
        {
          "field": "username",
          "message": "Username is required",
          "type": "missing"
        }
      ]
    },
    "timestamp": "2024-02-11T13:00:00Z",
    "path": "/api/v1/connections",
    "requestId": "req-12346"
  }
}
```

## Best Practices

### Do's

1. **Use specific exceptions** - Create custom exception types
2. **Provide context** - Include relevant details in errors
3. **Log errors properly** - Structured logging with context
4. **Validate early** - Validate inputs at boundaries
5. **Fail fast** - Don't let bad data propagate
6. **Handle errors at appropriate level** - Let exceptions bubble up to the right handler
7. **Clean up resources** - Use context managers and finally blocks
8. **Provide recovery mechanisms** - Allow retry or graceful degradation

### Don'ts

1. **Don't swallow exceptions** - Avoid empty except blocks
2. **Don't catch generic Exception** - Be specific about what you catch
3. **Don't leak sensitive information** - Don't expose stack traces in production
4. **Don't use exceptions for control flow** - Exceptions should be exceptional
5. **Don't log and re-raise without context** - Add context when re-raising
6. **Don't return error codes** - Use exceptions for errors
7. **Don't ignore return values** - Check return values that indicate errors

## Resources

- [Python Exception Hierarchy](https://docs.python.org/3/library/exceptions.html)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [HTTP Status Codes](https://httpstatuses.com/)
