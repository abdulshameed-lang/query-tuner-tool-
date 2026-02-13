# Naming Conventions

## Overview

Consistent naming conventions improve code readability and maintainability across the Oracle Database Performance Tuning Tool project.

## General Principles

### Be Descriptive
- Names should clearly indicate purpose
- Avoid abbreviations unless universally understood
- Be explicit rather than clever

### Be Consistent
- Follow established patterns in codebase
- Use same terminology throughout project
- Maintain conventions across languages

### Context Matters
- Longer names for wider scope
- Shorter names for tight loops
- Consider surrounding code

## Python Naming Conventions

### Variables

#### Local Variables
**Style**: `snake_case`

```python
# Good
elapsed_time = 1234.56
sql_statement = "SELECT * FROM users"
query_results = fetch_queries()
user_count = len(users)

# Bad
ElapsedTime = 1234.56  # PascalCase (use for classes)
sqlStatement = "SELECT * FROM users"  # camelCase (use in TypeScript)
q = fetch_queries()  # Too short
numberOfUsersInTheDatabase = len(users)  # Too long
```

#### Constants
**Style**: `UPPER_SNAKE_CASE`
**Location**: Module level

```python
# Good
MAX_CONNECTIONS = 20
DEFAULT_TIMEOUT_SECONDS = 300
ORACLE_SYS_SCHEMAS = ["SYS", "SYSTEM", "XDB"]
API_VERSION = "v1"

# Bad
max_connections = 20  # Should be uppercase
MaxConnections = 20  # Not snake_case
```

#### Boolean Variables
**Prefix**: `is_`, `has_`, `can_`, `should_`

```python
# Good
is_connected = True
has_execution_plan = False
can_execute_query = check_permissions()
should_retry = error_count < max_retries

# Bad
connected = True  # Unclear it's a boolean
execution_plan = False  # Sounds like data, not boolean
```

### Functions

**Style**: `snake_case`
**Pattern**: `verb_noun` or `verb`

```python
# Good - Action verbs
def get_query_details(sql_id: str) -> Query:
    ...

def calculate_elapsed_time(start: float, end: float) -> float:
    ...

def validate_sql_id(sql_id: str) -> bool:
    ...

# Good - Boolean functions
def is_valid_sql_id(sql_id: str) -> bool:
    ...

def has_execution_plan(sql_id: str) -> bool:
    ...

# Bad
def queryDetails(sql_id: str):  # camelCase
    ...

def CALCULATE(start, end):  # All caps
    ...

def query_details(sql_id: str):  # No verb
    ...
```

### Classes

**Style**: `PascalCase`
**Pattern**: Noun or noun phrase

```python
# Good
class QueryAnalyzer:
    ...

class ExecutionPlan:
    ...

class ConnectionManager:
    ...

class OracleConnectionError(Exception):
    ...

# Bad
class query_analyzer:  # snake_case
    ...

class analyze_query:  # Verb, not noun
    ...

class Analyze:  # Too vague
    ...
```

#### Exception Classes
**Suffix**: `Error`

```python
# Good
class QueryNotFoundError(Exception):
    ...

class OracleConnectionError(Exception):
    ...

class InvalidSqlIdError(ValueError):
    ...

# Bad
class QueryNotFound(Exception):  # Missing Error suffix
    ...

class OracleException(Exception):  # Use Error, not Exception
    ...
```

### Class Attributes and Methods

#### Instance Attributes
**Style**: `snake_case`

```python
class ConnectionManager:
    def __init__(self):
        self.host = "localhost"
        self.port = 1521
        self.connection_pool = None
```

#### Private Attributes/Methods
**Prefix**: Single underscore `_`

```python
class QueryAnalyzer:
    def __init__(self):
        self._cache = {}  # Private attribute
        self._connection = None

    def _fetch_from_oracle(self):  # Private method
        ...

    def get_queries(self):  # Public method
        return self._fetch_from_oracle()
```

#### Class Methods
**Decorator**: `@classmethod`

```python
class Query:
    @classmethod
    def from_oracle_row(cls, row):
        ...
```

#### Static Methods
**Decorator**: `@staticmethod`

```python
class QueryUtils:
    @staticmethod
    def format_sql_text(sql: str) -> str:
        ...
```

### Modules and Packages

**Style**: `snake_case`
**Pattern**: Short, descriptive nouns

```
# Good
connection.py
query_analyzer.py
execution_plans.py
wait_events.py

# Bad
Connection.py  # PascalCase
queryAnalyzer.py  # camelCase
qry_anlzr.py  # Over-abbreviated
```

### Files

**Style**: Match module/class name

```
# Modules
connection.py
query_analyzer.py

# React components
QueryList.tsx
ExecutionPlanTree.tsx

# Test files
test_connection.py
test_query_analyzer.py
QueryList.test.tsx
```

## TypeScript/React Naming Conventions

### Variables and Functions

**Style**: `camelCase`

```typescript
// Good
const queryList = fetchQueries();
const elapsedTime = 1234.56;
const isLoading = false;

function calculateTotalTime(queries: Query[]): number {
  return queries.reduce((sum, q) => sum + q.elapsedTime, 0);
}

// Bad
const QueryList = fetchQueries();  // PascalCase (use for components/classes)
const elapsed_time = 1234.56;  // snake_case (use in Python)
```

### Constants

**Style**: `UPPER_SNAKE_CASE` or `camelCase`

```typescript
// Good - Configuration constants
const MAX_QUERIES_PER_PAGE = 50;
const DEFAULT_TIMEOUT_MS = 5000;

// Good - Const objects (camelCase)
const apiEndpoints = {
  queries: '/api/v1/queries',
  plans: '/api/v1/execution-plans',
} as const;

// Bad
const max_queries_per_page = 50;  // snake_case
const MaxQueriesPerPage = 50;  // PascalCase
```

### Components

**Style**: `PascalCase`

```typescript
// Good
export const QueryList: React.FC<QueryListProps> = ({ queries }) => {
  ...
};

export const ExecutionPlanTree: React.FC<ExecutionPlanTreeProps> = ({ plan }) => {
  ...
};

// Bad
export const queryList = () => { ... };  // camelCase
export const query_list = () => { ... };  // snake_case
```

### Component Props

**Style**: Interface with `Props` suffix

```typescript
// Good
interface QueryCardProps {
  query: Query;
  onSelect: (sqlId: string) => void;
  isSelected?: boolean;
}

export const QueryCard: React.FC<QueryCardProps> = ({
  query,
  onSelect,
  isSelected = false
}) => {
  ...
};

// Bad
interface IQueryCard { ... }  // Hungarian notation
interface QueryCardProperties { ... }  // Too verbose
```

### Event Handlers

**Props**: Prefix with `on`
**Handlers**: Prefix with `handle`

```typescript
// Good
interface QueryCardProps {
  onClick: (sqlId: string) => void;
  onDelete: (sqlId: string) => void;
}

export const QueryCard: React.FC<QueryCardProps> = ({
  onClick,
  onDelete
}) => {
  const handleClick = () => {
    onClick(query.sqlId);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(query.sqlId);
  };

  return <div onClick={handleClick}>...</div>;
};

// Bad
interface QueryCardProps {
  clickHandler: () => void;  // Should be onClick
}

const clickTheCard = () => { ... };  // Should be handleClick
```

### Custom Hooks

**Prefix**: `use`

```typescript
// Good
export function useQueries(connectionId: string) {
  ...
}

export function useWebSocket(url: string) {
  ...
}

export function useDebounce<T>(value: T, delay: number) {
  ...
}

// Bad
export function getQueries() { ... }  // Missing 'use' prefix
export function queriesHook() { ... }  // 'use' should be prefix, not suffix
```

### Types and Interfaces

**Style**: `PascalCase`

```typescript
// Good - Interfaces for object shapes
interface Query {
  sqlId: string;
  sqlText: string;
  elapsedTime: number;
}

interface ExecutionPlan {
  sqlId: string;
  planHashValue: number;
  operations: PlanOperation[];
}

// Good - Types for unions, etc.
type QueryStatus = 'running' | 'completed' | 'failed';
type Nullable<T> = T | null;

// Bad
interface query { ... }  // lowercase
interface IQuery { ... }  // Hungarian notation
type query_status = 'running' | 'completed';  // snake_case
```

### Enums

**Style**: `PascalCase` for enum, `UPPER_SNAKE_CASE` for values

```typescript
// Good
enum QueryType {
  SELECT = 'SELECT',
  INSERT = 'INSERT',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
}

enum WaitEventClass {
  USER_IO = 'User I/O',
  SYSTEM_IO = 'System I/O',
  CONCURRENCY = 'Concurrency',
}

// Or use const object
const QueryType = {
  SELECT: 'SELECT',
  INSERT: 'INSERT',
  UPDATE: 'UPDATE',
  DELETE: 'DELETE',
} as const;
```

### Files and Folders

```
components/
  QueryList.tsx         # Component (PascalCase)
  QueryCard.tsx
  ExecutionPlanTree.tsx

hooks/
  useQueries.ts         # Hook (camelCase with 'use' prefix)
  useWebSocket.ts

utils/
  formatters.ts         # Utilities (camelCase)
  validators.ts

types/
  query.ts              # Type definitions (camelCase)
  executionPlan.ts
```

## API Naming Conventions

### Endpoints

**Style**: `lowercase-with-hyphens`
**Pattern**: Plural nouns for collections

```
# Good
GET /api/v1/queries
GET /api/v1/queries/{sql_id}
GET /api/v1/execution-plans
GET /api/v1/wait-events
POST /api/v1/connections

# Bad
GET /api/v1/Queries  # Capitalized
GET /api/v1/query  # Singular
GET /api/v1/getQueries  # Verb in URL
GET /api/v1/execution_plans  # Underscore
```

### Query Parameters

**Style**: `camelCase`

```
# Good
GET /api/v1/queries?sortBy=elapsedTime&order=desc&pageSize=20

# Bad
GET /api/v1/queries?sort_by=elapsedTime  # snake_case
GET /api/v1/queries?SortBy=elapsedTime  # PascalCase
```

### Request/Response Fields

**Style**: `camelCase`

```json
{
  "sqlId": "abc123",
  "sqlText": "SELECT * FROM users",
  "elapsedTime": 1234.56,
  "executionPlan": {
    "planHashValue": 12345,
    "operations": []
  }
}
```

## Database Naming Conventions

### Tables (if creating app database)

**Style**: `snake_case`, plural nouns

```sql
-- Good
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    created_at TIMESTAMP
);

-- Bad
CREATE TABLE UserSession (...);  -- PascalCase
CREATE TABLE user_session (...);  -- Singular
```

### Columns

**Style**: `snake_case`

```sql
-- Good
CREATE TABLE queries (
    sql_id VARCHAR(13),
    sql_text TEXT,
    elapsed_time NUMERIC,
    cpu_time NUMERIC,
    created_at TIMESTAMP
);
```

### Indexes

**Style**: `idx_table_column(s)`

```sql
-- Good
CREATE INDEX idx_queries_sql_id ON queries(sql_id);
CREATE INDEX idx_queries_elapsed_time ON queries(elapsed_time);

-- Bad
CREATE INDEX queries_idx ON queries(sql_id);
CREATE INDEX index1 ON queries(elapsed_time);
```

## Configuration and Environment Variables

**Style**: `UPPER_SNAKE_CASE`

```bash
# .env file
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=XEPDB1
ORACLE_USERNAME=monitor_user
ORACLE_PASSWORD=secure_password

DATABASE_URL=postgresql://localhost/querytuner
REDIS_URL=redis://localhost:6379

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

## Test Names

### Python Tests

**Pattern**: `test_<method>_<scenario>_<expected_result>`

```python
# Good
def test_create_pool_with_valid_credentials_returns_pool():
    ...

def test_create_pool_with_invalid_credentials_raises_error():
    ...

def test_get_queries_with_no_results_returns_empty_list():
    ...

# Bad
def test1():
    ...

def testCreatePool():
    ...

def test_create_pool():  # Not descriptive enough
    ...
```

### TypeScript Tests

**Pattern**: Same as Python but with spaces

```typescript
describe('QueryCard', () => {
  it('renders query information', () => {
    ...
  });

  it('calls onClick when clicked', () => {
    ...
  });

  it('highlights selected query', () => {
    ...
  });
});
```

## Abbreviations

### Acceptable Abbreviations

```
id - identifier
sql - Structured Query Language
api - Application Programming Interface
http - Hypertext Transfer Protocol
url - Uniform Resource Locator
json - JavaScript Object Notation
jwt - JSON Web Token
cpu - Central Processing Unit
io - Input/Output
db - Database
```

### Avoid These Abbreviations

```
# Bad
usr -> user
msg -> message
btn -> button
ctx -> context
cfg -> config
str -> string
num -> number
```

## Examples by Context

### Python Module

```python
"""Module for analyzing Oracle query performance."""

from typing import List, Optional
from dataclasses import dataclass

# Constants
MAX_QUERIES = 1000
DEFAULT_THRESHOLD_MS = 1000

# Data class
@dataclass
class QueryMetrics:
    """Metrics for a single query."""
    sql_id: str
    elapsed_time_ms: float
    execution_count: int
    cpu_time_ms: float

# Class
class QueryAnalyzer:
    """Analyzes Oracle query performance."""

    def __init__(self, connection_pool):
        self._connection_pool = connection_pool
        self._cache = {}

    def get_top_queries(
        self,
        top_n: int = 20,
        min_elapsed_ms: Optional[float] = None
    ) -> List[QueryMetrics]:
        """Retrieve top N queries by elapsed time."""
        ...

    def _fetch_from_oracle(self, sql: str) -> List:
        """Fetch data from Oracle (private method)."""
        ...

# Function
def calculate_average_elapsed_time(queries: List[QueryMetrics]) -> float:
    """Calculate average elapsed time across queries."""
    if not queries:
        return 0.0
    total = sum(q.elapsed_time_ms for q in queries)
    return total / len(queries)
```

### React Component

```typescript
import React, { useState, useCallback } from 'react';
import type { Query } from '@/types/query';

// Constants
const MAX_DISPLAYED_QUERIES = 100;
const DEFAULT_PAGE_SIZE = 20;

// Interface
interface QueryListProps {
  queries: Query[];
  onQuerySelect: (sqlId: string) => void;
  isLoading?: boolean;
}

// Component
export const QueryList: React.FC<QueryListProps> = ({
  queries,
  onQuerySelect,
  isLoading = false
}) => {
  // State
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Event handlers
  const handleQueryClick = useCallback((sqlId: string) => {
    setSelectedId(sqlId);
    onQuerySelect(sqlId);
  }, [onQuerySelect]);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  // Derived data
  const displayedQueries = queries.slice(
    (currentPage - 1) * DEFAULT_PAGE_SIZE,
    currentPage * DEFAULT_PAGE_SIZE
  );

  // Render
  return (
    <div className="query-list">
      {displayedQueries.map(query => (
        <QueryCard
          key={query.sqlId}
          query={query}
          isSelected={query.sqlId === selectedId}
          onClick={handleQueryClick}
        />
      ))}
    </div>
  );
};
```

## Resources

- [PEP 8 - Naming Conventions](https://pep8.org/#naming-conventions)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [TypeScript Naming Conventions](https://typescript-tv.com/naming-conventions/)
