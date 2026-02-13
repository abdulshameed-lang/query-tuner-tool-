# Python Style Guide

## Overview

This guide defines Python coding standards for the Oracle Database Performance Tuning Tool backend. We follow PEP 8 with project-specific extensions.

## Python Version

- **Required**: Python 3.11+
- **Rationale**: Modern type hints, performance improvements, better error messages

## Code Formatting

### Line Length
- **Maximum**: 88 characters (Black default)
- **Docstrings/Comments**: 72 characters

### Indentation
- **Use**: 4 spaces (never tabs)
- **Continuation**: Align with opening delimiter or use hanging indent

```python
# Good
result = some_function(
    arg1, arg2, arg3,
    arg4, arg5
)

# Also good
result = some_function(
    arg1,
    arg2,
    arg3,
)
```

### Blank Lines
- **2 blank lines**: Between top-level functions and classes
- **1 blank line**: Between methods in a class
- **1 blank line**: To separate logical sections in functions

## Imports

### Order (enforced by isort)
1. Standard library imports
2. Related third-party imports
3. Local application imports

```python
# Standard library
import os
import sys
from typing import Optional, List

# Third-party
from fastapi import FastAPI, HTTPException
import cx_Oracle

# Local
from app.core.oracle.connection import ConnectionManager
from app.models.query import Query
```

### Import Style
- Use absolute imports
- Avoid wildcard imports (`from module import *`)
- One import per line for `from` imports

```python
# Good
from typing import List, Optional, Dict

# Bad
from typing import *
```

## Type Hints

### Required Everywhere
- **Function signatures**: All parameters and return types
- **Class attributes**: When not obvious from assignment
- **Module-level variables**: When type is ambiguous

```python
from typing import Optional, List, Dict
from cx_Oracle import Connection

def get_top_queries(
    connection: Connection,
    top_n: int = 20,
    min_elapsed_time: Optional[float] = None
) -> List[Dict[str, Any]]:
    """Retrieve top N queries by elapsed time."""
    ...
```

### Type Hint Guidelines
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` for collections
- Use `Union[T1, T2]` for multiple possible types
- Use type aliases for complex types

```python
# Type aliases
ConnectionPool = cx_Oracle.SessionPool
QueryResult = Dict[str, Any]
QueryList = List[QueryResult]

def analyze_queries(pool: ConnectionPool) -> QueryList:
    ...
```

### Python 3.11+ Type Syntax
```python
# Use modern syntax where appropriate
def process_data(items: list[str]) -> dict[str, int]:
    ...

# Use | for Union (Python 3.10+)
def get_value(key: str) -> str | None:
    ...
```

## Naming Conventions

### General Rules
- **Descriptive names**: Be explicit, avoid abbreviations
- **Consistency**: Follow established patterns in the codebase

### Variables and Functions
- **Style**: `snake_case`
- **Private**: Prefix with single underscore `_private_method`

```python
# Good
def calculate_query_elapsed_time(sql_id: str) -> float:
    execution_count = get_execution_count(sql_id)
    total_elapsed = get_total_elapsed_time(sql_id)
    return total_elapsed / execution_count

# Bad
def calcQET(s: str) -> float:
    ec = getEC(s)
    te = getTET(s)
    return te / ec
```

### Classes
- **Style**: `PascalCase`
- **Exception classes**: Suffix with `Error`

```python
class QueryAnalyzer:
    pass

class OracleConnectionError(Exception):
    pass
```

### Constants
- **Style**: `UPPER_SNAKE_CASE`
- **Module level only**

```python
MAX_CONNECTION_POOL_SIZE = 20
DEFAULT_QUERY_TIMEOUT = 300
ORACLE_SYS_SCHEMAS = ["SYS", "SYSTEM", "XDB"]
```

### Private Attributes
- **Single underscore**: Internal use, but still accessible
- **Double underscore**: Name mangling (rarely needed)

```python
class ConnectionManager:
    def __init__(self):
        self._pool = None  # Internal use
        self.__secret = None  # Name mangled (rarely use)
```

## Docstrings

### Format: Google Style

```python
def get_execution_plan(sql_id: str, plan_hash_value: Optional[int] = None) -> Dict[str, Any]:
    """Retrieve execution plan for a SQL statement.

    Fetches the execution plan from V$SQL_PLAN view. If plan_hash_value
    is provided, retrieves that specific plan; otherwise retrieves the
    most recent plan.

    Args:
        sql_id: The SQL_ID of the statement.
        plan_hash_value: Optional specific plan hash value to retrieve.

    Returns:
        Dictionary containing execution plan tree structure with:
            - sql_id: The SQL identifier
            - plan_hash_value: Hash value of the plan
            - operations: List of plan operations
            - cost: Total cost estimate

    Raises:
        OracleConnectionError: If database connection fails.
        PlanNotFoundError: If the specified plan does not exist.

    Example:
        >>> plan = get_execution_plan("abc123xyz")
        >>> print(plan['cost'])
        1234
    """
    ...
```

### Docstring Requirements
- **All public functions**: Must have docstrings
- **All classes**: Must have docstrings
- **Complex private functions**: Should have docstrings
- **Simple getters/setters**: Docstring optional

## Error Handling

### Exception Hierarchy
- Create custom exceptions
- Inherit from appropriate base classes
- Include context in exception messages

```python
class QueryTunerError(Exception):
    """Base exception for Query Tuner Tool."""
    pass

class OracleConnectionError(QueryTunerError):
    """Raised when Oracle connection fails."""
    pass

class QueryAnalysisError(QueryTunerError):
    """Raised when query analysis fails."""
    pass
```

### Exception Handling Patterns
```python
# Be specific with exception types
try:
    connection = pool.acquire()
    result = execute_query(connection, sql)
except cx_Oracle.DatabaseError as e:
    error, = e.args
    raise OracleConnectionError(
        f"Database error: {error.code} - {error.message}"
    ) from e
finally:
    pool.release(connection)

# Use context managers when possible
from contextlib import contextmanager

@contextmanager
def get_connection(pool):
    connection = pool.acquire()
    try:
        yield connection
    finally:
        pool.release(connection)
```

### Don't Catch Generic Exceptions
```python
# Bad
try:
    process_data()
except Exception:
    pass

# Good
try:
    process_data()
except (ValueError, KeyError) as e:
    logger.error(f"Data processing failed: {e}")
    raise ProcessingError("Invalid data format") from e
```

## Logging

### Use Python logging module
```python
import logging

logger = logging.getLogger(__name__)

def process_query(sql_id: str) -> QueryResult:
    logger.info(f"Processing query: {sql_id}")
    try:
        result = analyze_query(sql_id)
        logger.debug(f"Query analysis complete: {result}")
        return result
    except QueryAnalysisError as e:
        logger.error(f"Query analysis failed for {sql_id}: {e}")
        raise
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: Confirmation that things are working
- **WARNING**: Something unexpected but handled
- **ERROR**: Error that caused operation failure
- **CRITICAL**: Serious error, application may crash

### Never Log Sensitive Data
```python
# Bad
logger.info(f"Connecting with password: {password}")

# Good
logger.info(f"Connecting to {host}:{port}/{service_name}")
```

## FastAPI-Specific Patterns

### Dependency Injection
```python
from fastapi import Depends, FastAPI
from app.core.oracle.connection import get_connection_pool

app = FastAPI()

def get_db_connection(pool = Depends(get_connection_pool)):
    """Dependency for database connection."""
    with pool.acquire() as conn:
        yield conn

@app.get("/queries")
async def get_queries(conn = Depends(get_db_connection)):
    return fetch_queries(conn)
```

### Async/Await
- Use `async def` for I/O-bound operations
- Use regular `def` for CPU-bound operations
- Don't mix async and sync unnecessarily

```python
from fastapi import APIRouter
import asyncio

router = APIRouter()

@router.get("/queries/{sql_id}")
async def get_query_details(sql_id: str):
    """Async endpoint for query details."""
    # Use asyncio for concurrent operations
    plan, stats, waits = await asyncio.gather(
        get_execution_plan_async(sql_id),
        get_query_stats_async(sql_id),
        get_wait_events_async(sql_id)
    )
    return {"plan": plan, "stats": stats, "waits": waits}
```

### Pydantic Models
```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class QueryRequest(BaseModel):
    """Request model for query analysis."""
    sql_id: str = Field(..., min_length=13, max_length=13)
    plan_hash_value: Optional[int] = Field(None, ge=0)

    @validator('sql_id')
    def validate_sql_id_format(cls, v):
        if not v.isalnum():
            raise ValueError('SQL_ID must be alphanumeric')
        return v.upper()

class QueryResponse(BaseModel):
    """Response model for query data."""
    sql_id: str
    sql_text: str
    elapsed_time: float
    executions: int

    class Config:
        orm_mode = True
```

## SQLAlchemy/cx_Oracle Patterns

### Use Bind Variables
```python
# Good - Prevents SQL injection
sql = "SELECT * FROM v$sql WHERE sql_id = :sql_id"
cursor.execute(sql, {"sql_id": sql_id})

# Bad - SQL injection risk
sql = f"SELECT * FROM v$sql WHERE sql_id = '{sql_id}'"
cursor.execute(sql)
```

### Connection Management
```python
import cx_Oracle

def create_connection_pool(dsn: str, user: str, password: str) -> cx_Oracle.SessionPool:
    """Create Oracle connection pool."""
    return cx_Oracle.SessionPool(
        user=user,
        password=password,
        dsn=dsn,
        min=5,
        max=20,
        increment=1,
        threaded=True,
        getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT
    )

def execute_query(pool: cx_Oracle.SessionPool, sql: str, params: dict) -> list:
    """Execute query with connection from pool."""
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
```

## Code Organization

### Module Structure
```python
"""Module docstring describing purpose.

Detailed description of module functionality and usage examples.
"""

# Imports
import standard_library
from third_party import module
from local import module

# Constants
CONSTANT_VALUE = 10

# Type aliases
TypeAlias = Dict[str, Any]

# Classes
class MainClass:
    pass

# Functions
def main_function():
    pass

# Main execution
if __name__ == "__main__":
    main()
```

### File Organization
- One class per file (for large classes)
- Group related functions in modules
- Keep files under 500 lines when possible

## Testing Conventions

### Test File Structure
```python
import pytest
from app.core.oracle.connection import ConnectionManager

class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.fixture
    def connection_manager(self):
        """Fixture for ConnectionManager instance."""
        return ConnectionManager(
            dsn="localhost:1521/XEPDB1",
            user="test_user",
            password="test_pass"
        )

    def test_create_pool_success(self, connection_manager):
        """Test successful connection pool creation."""
        pool = connection_manager.create_pool()
        assert pool is not None
        assert pool.min == 5

    def test_create_pool_invalid_credentials(self):
        """Test pool creation with invalid credentials."""
        manager = ConnectionManager(dsn="invalid", user="bad", password="bad")
        with pytest.raises(OracleConnectionError):
            manager.create_pool()
```

### Test Naming
- **Pattern**: `test_<method>_<condition>_<expected_result>`
- **Be descriptive**: Test name should describe what is tested

## Performance Best Practices

### Use Generators for Large Data
```python
# Good - Memory efficient
def get_all_queries(connection) -> Generator[Dict[str, Any], None, None]:
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM v$sql")
    for row in cursor:
        yield parse_query_row(row)

# Bad - Loads everything into memory
def get_all_queries(connection) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM v$sql")
    return [parse_query_row(row) for row in cursor.fetchall()]
```

### Use List Comprehensions
```python
# Good
result = [process(item) for item in items if item.is_valid()]

# Acceptable for complex logic
result = []
for item in items:
    if item.is_valid():
        processed = process(item)
        if processed:
            result.append(processed)
```

### Avoid Premature Optimization
- Write clear code first
- Profile before optimizing
- Document performance-critical sections

## Code Comments

### When to Comment
- **Why, not what**: Explain reasoning, not obvious code
- **Complex algorithms**: Explain approach
- **Workarounds**: Explain why workaround is needed
- **TODO/FIXME**: Mark temporary code

```python
# Good - Explains why
# Using V$SQL instead of DBA_HIST_SQLSTAT because we need real-time data
sql = "SELECT * FROM v$sql WHERE elapsed_time > :threshold"

# Bad - Explains obvious
# Get the SQL from the database
sql = "SELECT * FROM v$sql"
```

### TODO Comments
```python
# TODO(username): Add support for RAC environments
# FIXME(username): This fails when sql_id contains special characters
# HACK(username): Temporary workaround for Oracle bug 12345678
```

## Code Review Checklist

Before submitting code, ensure:
- [ ] All functions have type hints
- [ ] Public functions have docstrings
- [ ] No unused imports or variables
- [ ] Tests are written and passing
- [ ] Code is formatted with Black
- [ ] Imports are sorted with isort
- [ ] No pylint or flake8 warnings
- [ ] No security vulnerabilities

## Tools Configuration

### black
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
```

### isort
```toml
# pyproject.toml
[tool.isort]
profile = "black"
line_length = 88
```

### mypy
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### pylint
```toml
# pyproject.toml
[tool.pylint.messages_control]
max-line-length = 88
disable = [
    "C0330",  # Wrong hanging indentation (conflicts with Black)
    "C0326",  # Bad whitespace (conflicts with Black)
]
```

## Resources

- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [cx_Oracle Documentation](https://cx-oracle.readthedocs.io/)
