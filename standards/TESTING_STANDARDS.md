# Testing Standards

## Overview

This document defines testing conventions, strategies, and requirements for the Oracle Database Performance Tuning Tool.

## Testing Philosophy

### Test Pyramid
- **Unit Tests (70%)**: Fast, isolated, test individual functions/methods
- **Integration Tests (20%)**: Test component interactions
- **End-to-End Tests (10%)**: Test complete user workflows

### Core Principles
- **Write tests first** (TDD when appropriate)
- **Tests are documentation** - they show how code should be used
- **Fast feedback** - tests should run quickly
- **Reliable** - no flaky tests
- **Maintainable** - easy to understand and update

## Code Coverage Requirements

### Minimum Coverage
- **Overall**: 80% code coverage
- **Critical modules**: 90% coverage
  - `backend/app/core/oracle/connection.py`
  - `backend/app/core/analysis/query_analyzer.py`
  - `backend/app/core/oracle/execution_plans.py`
- **New code**: 85% coverage

### Coverage Tools
```bash
# Backend (Python)
pytest --cov=app --cov-report=html --cov-report=term

# Frontend (TypeScript)
npm run test:coverage
```

## Backend Testing (Python)

### Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_connection.py
│   ├── test_query_analyzer.py
│   └── test_execution_plans.py
├── integration/             # Integration tests
│   ├── test_api_queries.py
│   └── test_oracle_integration.py
└── performance/             # Performance tests
    └── test_query_performance.py
```

### Naming Conventions

#### Test Files
- **Pattern**: `test_<module_name>.py`
- **Example**: `test_connection.py`, `test_query_analyzer.py`

#### Test Classes
- **Pattern**: `Test<ClassName>`
- **Example**: `TestConnectionManager`, `TestQueryAnalyzer`

#### Test Functions
- **Pattern**: `test_<method>_<scenario>_<expected_result>`
- **Be descriptive**: Name should explain what is tested

```python
def test_create_pool_with_valid_credentials_returns_pool()
def test_create_pool_with_invalid_credentials_raises_error()
def test_get_queries_with_no_results_returns_empty_list()
def test_get_queries_with_timeout_raises_timeout_error()
```

### Test Structure (Arrange-Act-Assert)

```python
import pytest
from app.core.oracle.connection import ConnectionManager
from app.core.exceptions import OracleConnectionError

class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_create_pool_success(self):
        """Test successful connection pool creation."""
        # Arrange
        manager = ConnectionManager(
            dsn="localhost:1521/XEPDB1",
            user="test_user",
            password="test_pass"
        )

        # Act
        pool = manager.create_pool()

        # Assert
        assert pool is not None
        assert pool.min == 5
        assert pool.max == 20

    def test_create_pool_invalid_credentials(self):
        """Test pool creation with invalid credentials."""
        # Arrange
        manager = ConnectionManager(
            dsn="invalid",
            user="bad_user",
            password="bad_pass"
        )

        # Act & Assert
        with pytest.raises(OracleConnectionError) as exc_info:
            manager.create_pool()

        assert "Invalid credentials" in str(exc_info.value)
```

### Fixtures

Use pytest fixtures for reusable test setup:

```python
# conftest.py
import pytest
from app.core.oracle.connection import ConnectionManager

@pytest.fixture
def connection_manager():
    """Fixture for ConnectionManager instance."""
    return ConnectionManager(
        dsn="localhost:1521/XEPDB1",
        user="test_user",
        password="test_pass"
    )

@pytest.fixture
def mock_connection(mocker):
    """Fixture for mocked Oracle connection."""
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn

@pytest.fixture
def sample_queries():
    """Fixture for sample query data."""
    return [
        {
            "sql_id": "abc123",
            "sql_text": "SELECT * FROM users",
            "elapsed_time": 1000,
            "executions": 10
        },
        {
            "sql_id": "def456",
            "sql_text": "UPDATE orders SET status = :1",
            "elapsed_time": 800,
            "executions": 5
        }
    ]

# Usage in tests
def test_get_queries(connection_manager, sample_queries):
    """Test query retrieval."""
    queries = connection_manager.get_queries()
    assert len(queries) == len(sample_queries)
```

### Mocking

Use `pytest-mock` for mocking dependencies:

```python
def test_fetch_queries_calls_oracle(mocker, connection_manager):
    """Test that fetch_queries calls Oracle correctly."""
    # Mock the execute method
    mock_execute = mocker.patch.object(
        connection_manager,
        'execute_query',
        return_value=[("abc123", "SELECT * FROM users", 1000)]
    )

    # Call method
    result = connection_manager.fetch_queries(min_elapsed=1000)

    # Assert mock was called correctly
    mock_execute.assert_called_once()
    args, kwargs = mock_execute.call_args
    assert kwargs['min_elapsed'] == 1000
```

### Parametrized Tests

Test multiple scenarios with one test function:

```python
@pytest.mark.parametrize("sql_id,expected_length", [
    ("abc123xyz4567", 13),
    ("ABC123XYZ4567", 13),
    ("abcdefghijklm", 13),
])
def test_sql_id_validation_valid(sql_id, expected_length):
    """Test SQL_ID validation with valid inputs."""
    assert len(sql_id) == expected_length
    assert sql_id.isalnum()

@pytest.mark.parametrize("sql_id,error_message", [
    ("", "SQL_ID cannot be empty"),
    ("abc", "SQL_ID must be 13 characters"),
    ("abc123xyz45!!", "SQL_ID must be alphanumeric"),
])
def test_sql_id_validation_invalid(sql_id, error_message):
    """Test SQL_ID validation with invalid inputs."""
    with pytest.raises(ValidationError) as exc_info:
        validate_sql_id(sql_id)
    assert error_message in str(exc_info.value)
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_get_queries():
    """Test async query retrieval."""
    result = await get_queries_async("conn-123")
    assert len(result) > 0

@pytest.mark.asyncio
async def test_async_timeout():
    """Test async operation timeout."""
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_query(), timeout=1.0)
```

### Testing Exceptions

```python
def test_invalid_connection_raises_error():
    """Test that invalid connection raises appropriate error."""
    with pytest.raises(OracleConnectionError) as exc_info:
        connect_to_oracle("invalid_dsn", "user", "pass")

    # Check error message
    assert "Failed to connect" in str(exc_info.value)

    # Check error code if custom exception
    assert exc_info.value.code == "CONNECTION_FAILED"
```

## Frontend Testing (TypeScript/React)

### Test Structure

```
frontend/tests/
├── unit/
│   ├── components/
│   │   ├── QueryCard.test.tsx
│   │   └── QueryList.test.tsx
│   ├── hooks/
│   │   └── useQueries.test.ts
│   └── utils/
│       └── formatters.test.ts
├── integration/
│   └── pages/
│       └── QueriesPage.test.tsx
└── e2e/
    ├── connection.cy.ts
    └── queries.cy.ts
```

### Component Tests

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryCard } from './QueryCard';
import type { Query } from '@/types/query';

describe('QueryCard', () => {
  const mockQuery: Query = {
    sqlId: 'abc123xyz4567',
    sqlText: 'SELECT * FROM users WHERE id = :1',
    elapsedTime: 1234.56,
    executions: 100,
    cpuTime: 987.65,
  };

  it('renders query information', () => {
    render(<QueryCard query={mockQuery} onClick={jest.fn()} />);

    expect(screen.getByText(/abc123xyz4567/)).toBeInTheDocument();
    expect(screen.getByText(/SELECT \* FROM users/)).toBeInTheDocument();
    expect(screen.getByText(/1234.56/)).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<QueryCard query={mockQuery} onClick={handleClick} />);

    fireEvent.click(screen.getByRole('article'));
    expect(handleClick).toHaveBeenCalledWith('abc123xyz4567');
  });

  it('highlights selected query', () => {
    const { container } = render(
      <QueryCard query={mockQuery} onClick={jest.fn()} isSelected={true} />
    );

    expect(container.firstChild).toHaveClass('selected');
  });
});
```

### Hook Tests

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useQueries } from './useQueries';

describe('useQueries', () => {
  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  it('fetches queries on mount', async () => {
    const { result } = renderHook(() => useQueries('conn-123'), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.queries).toHaveLength(5);
  });

  it('handles error state', async () => {
    // Mock API to return error
    jest.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('API Error'));

    const { result } = renderHook(() => useQueries('conn-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    expect(result.current.error?.message).toBe('API Error');
  });
});
```

### Utility Function Tests

```typescript
import { formatElapsedTime, formatBytes } from './formatters';

describe('formatters', () => {
  describe('formatElapsedTime', () => {
    it('formats milliseconds correctly', () => {
      expect(formatElapsedTime(1234)).toBe('1.23s');
      expect(formatElapsedTime(567)).toBe('567ms');
      expect(formatElapsedTime(1234567)).toBe('20m 34s');
    });

    it('handles zero', () => {
      expect(formatElapsedTime(0)).toBe('0ms');
    });

    it('handles negative values', () => {
      expect(formatElapsedTime(-100)).toBe('0ms');
    });
  });

  describe('formatBytes', () => {
    it('formats bytes correctly', () => {
      expect(formatBytes(1024)).toBe('1 KB');
      expect(formatBytes(1048576)).toBe('1 MB');
      expect(formatBytes(1073741824)).toBe('1 GB');
    });
  });
});
```

### Snapshot Testing

```typescript
import { render } from '@testing-library/react';
import { ExecutionPlanTree } from './ExecutionPlanTree';

describe('ExecutionPlanTree', () => {
  it('matches snapshot', () => {
    const plan = {
      sqlId: 'abc123',
      operations: [
        { id: 0, operation: 'SELECT STATEMENT', cost: 100 },
        { id: 1, parentId: 0, operation: 'TABLE ACCESS FULL', cost: 100 },
      ],
    };

    const { container } = render(<ExecutionPlanTree plan={plan} />);
    expect(container).toMatchSnapshot();
  });
});
```

## Integration Tests

### API Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_queries_endpoint():
    """Test GET /api/v1/queries endpoint."""
    response = client.get("/api/v1/queries?top=10")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) <= 10

def test_get_query_details_not_found():
    """Test GET /api/v1/queries/{sql_id} with non-existent ID."""
    response = client.get("/api/v1/queries/nonexistent123")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "QUERY_NOT_FOUND"

def test_get_execution_plan():
    """Test GET /api/v1/execution-plans/{sql_id}."""
    response = client.get("/api/v1/execution-plans/abc123xyz4567")

    assert response.status_code == 200
    data = response.json()["data"]
    assert "sqlId" in data
    assert "operations" in data
```

### Database Integration Tests

```python
@pytest.fixture(scope="session")
def test_db():
    """Create test database connection."""
    pool = create_test_connection_pool()
    yield pool
    pool.close()

def test_fetch_queries_from_db(test_db):
    """Test fetching queries from actual Oracle database."""
    with test_db.acquire() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sql_id, sql_text, elapsed_time
            FROM v$sql
            WHERE rownum <= 10
        """)
        results = cursor.fetchall()

    assert len(results) > 0
    assert len(results[0]) == 3  # 3 columns
```

## End-to-End Tests (Cypress)

```typescript
// cypress/e2e/queries.cy.ts
describe('Queries Page', () => {
  beforeEach(() => {
    cy.visit('/queries');
  });

  it('displays list of queries', () => {
    cy.get('[data-testid="query-card"]').should('have.length.at.least', 1);
  });

  it('filters queries by elapsed time', () => {
    cy.get('[data-testid="filter-elapsed-time"]').type('1000');
    cy.get('[data-testid="apply-filter"]').click();

    cy.get('[data-testid="query-card"]').each(($el) => {
      cy.wrap($el)
        .find('[data-testid="elapsed-time"]')
        .invoke('text')
        .then((text) => {
          const value = parseFloat(text);
          expect(value).to.be.at.least(1000);
        });
    });
  });

  it('navigates to query details', () => {
    cy.get('[data-testid="query-card"]').first().click();
    cy.url().should('include', '/queries/');
    cy.get('[data-testid="query-details"]').should('be.visible');
  });
});
```

## Performance Tests

```python
import pytest
from locust import HttpUser, task, between

class QueryTunerUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_queries(self):
        self.client.get("/api/v1/queries?top=20")

    @task(1)
    def view_query_details(self):
        self.client.get("/api/v1/queries/abc123xyz4567")

    @task(1)
    def view_execution_plan(self):
        self.client.get("/api/v1/execution-plans/abc123xyz4567")

# Run with: locust -f locustfile.py --host=http://localhost:8000
```

## Test Data Management

### Fixtures and Factories

```python
# test_factories.py
from dataclasses import dataclass

@dataclass
class QueryFactory:
    """Factory for creating test Query objects."""

    @staticmethod
    def create(sql_id="abc123xyz4567", **kwargs):
        defaults = {
            "sql_text": "SELECT * FROM users",
            "elapsed_time": 1000.0,
            "executions": 10,
            "cpu_time": 800.0,
        }
        defaults.update(kwargs)
        return Query(sql_id=sql_id, **defaults)

# Usage
def test_query_analysis():
    query = QueryFactory.create(elapsed_time=5000)
    result = analyze_query(query)
    assert result.needs_tuning is True
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements/test.txt
      - run: pytest backend/tests --cov --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test -- --coverage
```

## Best Practices

1. **Write tests before fixing bugs** - Create failing test, then fix
2. **Keep tests independent** - Tests should not depend on each other
3. **Use meaningful assertions** - Clear assertion messages
4. **Test edge cases** - Not just happy path
5. **Mock external dependencies** - Oracle, Redis, external APIs
6. **Keep tests fast** - Unit tests should run in milliseconds
7. **Clean up after tests** - Use fixtures and teardown
8. **Avoid test interdependencies**
9. **Test one thing per test** - Focused tests
10. **Use descriptive test names**

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Jest Documentation](https://jestjs.io/)
- [Cypress Documentation](https://docs.cypress.io/)
