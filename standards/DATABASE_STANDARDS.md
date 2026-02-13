# Database Standards

## Overview

This document defines Oracle database query standards, optimization guidelines, and best practices for the Query Tuner Tool.

## Oracle Query Best Practices

### Always Use Bind Variables

**Why**: Prevents SQL injection and improves performance through cursor sharing.

```python
# Good - Using bind variables
sql = """
    SELECT sql_id, sql_text, elapsed_time
    FROM v$sql
    WHERE elapsed_time > :min_time
    AND executions > :min_execs
"""
cursor.execute(sql, {"min_time": 1000, "min_execs": 10})

# Bad - String concatenation (SQL injection risk!)
sql = f"""
    SELECT sql_id, sql_text, elapsed_time
    FROM v$sql
    WHERE elapsed_time > {min_time}
"""
cursor.execute(sql)
```

### Use Appropriate Oracle Data Types

```python
# Bind variable types
cursor.setinputsizes(
    sql_id=cx_Oracle.STRING,
    elapsed_time=cx_Oracle.NUMBER,
    sample_time=cx_Oracle.TIMESTAMP
)
```

## Connection Management

### Connection Pooling

Always use connection pooling for better performance and resource management.

```python
# Create connection pool
pool = cx_Oracle.SessionPool(
    user=username,
    password=password,
    dsn=dsn,
    min=5,                    # Minimum connections
    max=20,                   # Maximum connections
    increment=1,              # How many to add when pool exhausted
    threaded=True,           # Thread-safe
    getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT,  # Wait for connection
    timeout=300,             # Connection timeout (seconds)
    wait_timeout=10000,      # Wait timeout for connection (ms)
    max_lifetime_session=3600  # Max session lifetime (seconds)
)

# Acquire connection from pool
connection = pool.acquire()
try:
    # Use connection
    cursor = connection.cursor()
    cursor.execute(sql, params)
    result = cursor.fetchall()
finally:
    # Always release connection back to pool
    pool.release(connection)
```

### Context Managers

Use context managers for automatic resource cleanup:

```python
from contextlib import contextmanager

@contextmanager
def get_connection(pool):
    """Context manager for database connections."""
    connection = pool.acquire()
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        pool.release(connection)

# Usage
with get_connection(pool) as conn:
    cursor = conn.cursor()
    cursor.execute(sql, params)
    result = cursor.fetchall()
```

### Cursor Management

Always close cursors to free resources:

```python
# Good - Using context manager
with connection.cursor() as cursor:
    cursor.execute(sql, params)
    result = cursor.fetchall()
# Cursor automatically closed

# Also good - Explicit close
cursor = connection.cursor()
try:
    cursor.execute(sql, params)
    result = cursor.fetchall()
finally:
    cursor.close()
```

## Query Optimization

### Query Timeouts

Set query timeouts to prevent long-running queries from blocking:

```python
# Set statement timeout
cursor = connection.cursor()
cursor.execute("ALTER SESSION SET MAX_DUMP_FILE_SIZE = UNLIMITED")
cursor.execute("ALTER SESSION SET SQL_TRACE = TRUE")

# Call timeout parameter (milliseconds)
cursor.callTimeout = 30000  # 30 seconds
```

### Fetch Size

Optimize fetch size for large result sets:

```python
# Set fetch size for better performance
cursor = connection.cursor()
cursor.arraysize = 1000  # Fetch 1000 rows at a time

cursor.execute(sql, params)
while True:
    rows = cursor.fetchmany()
    if not rows:
        break
    for row in rows:
        process_row(row)
```

### Use Appropriate Fetch Methods

```python
# fetchone() - Single row
cursor.execute("SELECT COUNT(*) FROM v$sql")
count = cursor.fetchone()[0]

# fetchall() - All rows (use for small result sets)
cursor.execute("SELECT * FROM v$sql WHERE rownum <= 100")
rows = cursor.fetchall()

# fetchmany() - Batch fetching (use for large result sets)
cursor.execute("SELECT * FROM v$sql")
while True:
    rows = cursor.fetchmany(100)
    if not rows:
        break
    process_rows(rows)
```

## Oracle System Views

### V$ Views (Real-Time)

```sql
-- V$SQL - Current SQL in shared pool
SELECT sql_id, sql_text, elapsed_time, executions, cpu_time,
       buffer_gets, disk_reads, rows_processed
FROM v$sql
WHERE elapsed_time > :threshold
ORDER BY elapsed_time DESC;

-- V$SESSION - Active sessions
SELECT sid, serial#, username, program, machine, status,
       sql_id, event, wait_class, seconds_in_wait
FROM v$session
WHERE username IS NOT NULL
AND status = 'ACTIVE';

-- V$SQL_PLAN - Execution plans
SELECT sql_id, plan_hash_value, id, parent_id,
       operation, options, object_name,
       cost, cardinality, bytes
FROM v$sql_plan
WHERE sql_id = :sql_id
ORDER BY id;

-- V$ACTIVE_SESSION_HISTORY - Recent wait events
SELECT session_id, sql_id, event, wait_class,
       time_waited, wait_time_micro
FROM v$active_session_history
WHERE sample_time > SYSDATE - INTERVAL '5' MINUTE;
```

### DBA_ Views (Metadata)

```sql
-- DBA_TAB_STATISTICS - Table statistics
SELECT owner, table_name, num_rows, blocks, last_analyzed,
       stale_stats
FROM dba_tab_statistics
WHERE owner NOT IN ('SYS', 'SYSTEM')
AND (stale_stats = 'YES' OR last_analyzed < SYSDATE - 7);

-- DBA_IND_STATISTICS - Index statistics
SELECT owner, index_name, table_name, num_rows, last_analyzed,
       stale_stats
FROM dba_ind_statistics
WHERE owner NOT IN ('SYS', 'SYSTEM');
```

### DBA_HIST_ Views (AWR Historical Data)

```sql
-- DBA_HIST_SQLSTAT - Historical SQL performance
SELECT sql_id, plan_hash_value,
       SUM(elapsed_time_delta) as total_elapsed,
       SUM(executions_delta) as total_executions,
       SUM(cpu_time_delta) as total_cpu
FROM dba_hist_sqlstat
WHERE snap_id BETWEEN :start_snap AND :end_snap
GROUP BY sql_id, plan_hash_value
ORDER BY total_elapsed DESC;

-- DBA_HIST_ACTIVE_SESS_HISTORY - Historical wait events
SELECT sql_id, event, wait_class,
       COUNT(*) as sample_count,
       SUM(time_waited) as total_wait_time
FROM dba_hist_active_sess_history
WHERE sample_time BETWEEN :start_time AND :end_time
AND sql_id = :sql_id
GROUP BY sql_id, event, wait_class;
```

## Required Oracle Privileges

### Minimum Required Privileges

```sql
-- Create monitoring user
CREATE USER query_monitor IDENTIFIED BY secure_password;

-- Grant necessary system privileges
GRANT CREATE SESSION TO query_monitor;
GRANT SELECT ANY DICTIONARY TO query_monitor;
GRANT SELECT_CATALOG_ROLE TO query_monitor;

-- Grant specific object privileges
GRANT SELECT ON v_$sql TO query_monitor;
GRANT SELECT ON v_$sql_plan TO query_monitor;
GRANT SELECT ON v_$session TO query_monitor;
GRANT SELECT ON v_$active_session_history TO query_monitor;
GRANT SELECT ON v_$session_wait TO query_monitor;
GRANT SELECT ON v_$lock TO query_monitor;
GRANT SELECT ON v_$sesstat TO query_monitor;
GRANT SELECT ON v_$statname TO query_monitor;
GRANT SELECT ON v_$version TO query_monitor;

-- Grant AWR/ASH privileges (requires Diagnostics Pack license)
GRANT SELECT ON dba_hist_sqlstat TO query_monitor;
GRANT SELECT ON dba_hist_sql_plan TO query_monitor;
GRANT SELECT ON dba_hist_active_sess_history TO query_monitor;
GRANT SELECT ON dba_hist_snapshot TO query_monitor;

-- Grant statistics privileges
GRANT SELECT ON dba_tab_statistics TO query_monitor;
GRANT SELECT ON dba_ind_statistics TO query_monitor;
GRANT SELECT ON dba_tables TO query_monitor;
GRANT SELECT ON dba_indexes TO query_monitor;
GRANT SELECT ON dba_scheduler_jobs TO query_monitor;
```

## Transaction Management

### Read-Only Queries

For monitoring queries, use read-only transactions:

```python
# Set transaction to read-only
connection.begin()
cursor = connection.cursor()
cursor.execute("SET TRANSACTION READ ONLY")

try:
    # Execute monitoring queries
    cursor.execute(query1, params1)
    result1 = cursor.fetchall()

    cursor.execute(query2, params2)
    result2 = cursor.fetchall()

    connection.commit()
except Exception:
    connection.rollback()
    raise
```

### No Modifications

**This tool should NEVER modify Oracle data**:
- No INSERT statements
- No UPDATE statements
- No DELETE statements
- No DDL (CREATE, ALTER, DROP)
- No DCL (GRANT, REVOKE) except during setup
- Read-only access only

## Error Handling

### Oracle-Specific Exceptions

```python
import cx_Oracle

try:
    cursor.execute(sql, params)
except cx_Oracle.DatabaseError as e:
    error, = e.args
    if error.code == 1017:  # ORA-01017: invalid username/password
        raise AuthenticationError("Invalid credentials")
    elif error.code == 12541:  # ORA-12541: TNS:no listener
        raise ConnectionError("Database listener not available")
    elif error.code == 942:  # ORA-00942: table or view does not exist
        raise PrivilegeError("Insufficient privileges or view not found")
    else:
        raise OracleError(f"Oracle error {error.code}: {error.message}")
```

### Common Oracle Error Codes

```python
ORACLE_ERROR_CODES = {
    900: "Invalid SQL statement",
    904: "Invalid column name",
    936: "Missing expression",
    942: "Table or view does not exist",
    1017: "Invalid username/password",
    1031: "Insufficient privileges",
    1033: "Oracle initialization or shutdown in progress",
    1034: "Oracle not available",
    12154: "TNS:could not resolve service name",
    12541: "TNS:no listener",
    12543: "TNS:destination host unreachable",
}
```

## SQL Formatting

### Query Formatting Standards

```sql
-- Good formatting
SELECT
    s.sql_id,
    s.sql_text,
    s.elapsed_time / 1000000 AS elapsed_seconds,
    s.executions,
    s.cpu_time / 1000000 AS cpu_seconds,
    ROUND(s.buffer_gets / NULLIF(s.executions, 0), 2) AS avg_buffer_gets
FROM
    v$sql s
WHERE
    s.elapsed_time > :min_elapsed_time
    AND s.executions > :min_executions
    AND s.parsing_schema_name NOT IN ('SYS', 'SYSTEM')
ORDER BY
    s.elapsed_time DESC
FETCH FIRST :top_n ROWS ONLY;
```

### Naming Conventions

- Use lowercase for SQL keywords (optional, but consistent)
- Use meaningful table aliases
- Align columns and conditions for readability

## Performance Considerations

### Limit Result Sets

Always limit large result sets:

```sql
-- Use ROWNUM or FETCH FIRST
SELECT * FROM v$sql
WHERE rownum <= 100;

-- Or (12c+)
SELECT * FROM v$sql
FETCH FIRST 100 ROWS ONLY;

-- Use pagination for large datasets
SELECT * FROM v$sql
ORDER BY elapsed_time DESC
OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY;
```

### Avoid SELECT *

Select only needed columns:

```sql
-- Good
SELECT sql_id, sql_text, elapsed_time
FROM v$sql;

-- Bad (wastes bandwidth and memory)
SELECT * FROM v$sql;
```

### Use EXISTS Instead of COUNT

```sql
-- Good - Stops at first match
SELECT CASE
    WHEN EXISTS (
        SELECT 1 FROM v$sql WHERE sql_id = :sql_id
    ) THEN 1
    ELSE 0
END AS sql_exists
FROM dual;

-- Bad - Counts all matches
SELECT COUNT(*) FROM v$sql WHERE sql_id = :sql_id;
```

## Caching Strategy

### Cache Expensive Queries

```python
import time
from functools import lru_cache

# Cache query results with TTL
def cache_with_ttl(seconds=30):
    def decorator(func):
        cache = {}
        cache_time = {}

        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()

            if key in cache and (now - cache_time[key]) < seconds:
                return cache[key]

            result = func(*args, **kwargs)
            cache[key] = result
            cache_time[key] = now
            return result

        return wrapper
    return decorator

@cache_with_ttl(seconds=30)
def get_top_queries(connection, top_n=20):
    """Cache top queries for 30 seconds."""
    cursor = connection.cursor()
    cursor.execute(TOP_QUERIES_SQL, {"top_n": top_n})
    return cursor.fetchall()
```

## Testing with Oracle

### Use Oracle XE for Testing

```python
# Test configuration
TEST_DSN = "localhost:1521/XEPDB1"
TEST_USER = "test_monitor"
TEST_PASSWORD = "test_password"

# Create test connection pool
def create_test_pool():
    return cx_Oracle.SessionPool(
        user=TEST_USER,
        password=TEST_PASSWORD,
        dsn=TEST_DSN,
        min=1,
        max=5,
        increment=1
    )
```

### Mock Oracle Connections in Tests

```python
from unittest.mock import Mock, patch

def test_get_queries():
    # Mock cursor
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        ("abc123", "SELECT * FROM users", 1000, 10)
    ]

    # Mock connection
    mock_conn = Mock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Test function
    result = get_queries(mock_conn)
    assert len(result) == 1
```

## Security Best Practices

1. **Never log passwords or credentials**
2. **Use Oracle Wallet for credential storage**
3. **Always use bind variables**
4. **Limit privileges to read-only**
5. **Use dedicated monitoring user**
6. **Implement connection timeouts**
7. **Validate all inputs**
8. **Use SSL/TLS for connections** (Oracle Native Network Encryption)

## Resources

- [cx_Oracle Documentation](https://cx-oracle.readthedocs.io/)
- [Oracle Database SQL Reference](https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/)
- [Oracle Performance Tuning Guide](https://docs.oracle.com/en/database/oracle/oracle-database/21/tgdba/)
- [V$ and DBA_ Views Reference](https://docs.oracle.com/en/database/oracle/oracle-database/21/refrn/)
