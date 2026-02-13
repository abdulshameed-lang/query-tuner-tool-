# Backend Tests

This directory contains all backend tests for the Query Tuner Tool.

## Test Structure

```
tests/
├── unit/              # Unit tests (isolated, mocked dependencies)
│   ├── core/         # Tests for core modules
│   ├── services/     # Tests for service layer
│   └── api/          # Tests for API utilities
├── integration/       # Integration tests (real dependencies)
│   ├── api/          # API endpoint integration tests
│   └── oracle/       # Oracle database integration tests
└── conftest.py       # Shared pytest fixtures
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=app --cov-report=html
```

### Run specific test types
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Tests for a specific module
pytest tests/unit/services/test_query_service.py

# Run a specific test
pytest tests/unit/services/test_query_service.py::TestQueryService::test_get_queries_default_params
```

### Run tests in parallel (faster)
```bash
pytest -n auto
```

### Run with verbose output
```bash
pytest -v
```

### Run and stop on first failure
```bash
pytest -x
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, real dependencies)
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.oracle` - Tests requiring Oracle database connection

## Writing Tests

### Unit Tests

Unit tests should:
- Be fast (< 1 second each)
- Mock all external dependencies
- Test a single unit of code in isolation
- Have clear, descriptive names

Example:
```python
def test_calculate_impact_score_high_values(query_service):
    """Test impact score with high resource usage."""
    query = {
        "elapsed_time": 10000000000,
        "cpu_time": 8000000000,
    }

    result = query_service._calculate_impact_score(query)

    assert result["impact_score"] > 50
    assert result["needs_tuning"] is True
```

### Integration Tests

Integration tests should:
- Test multiple components working together
- Use real dependencies where appropriate
- Test API endpoints end-to-end
- Verify database interactions

Example:
```python
def test_get_queries_default(client, mock_query_service):
    """Test GET /queries with default parameters."""
    mock_query_service.get_queries.return_value = (sample_queries, 2)

    response = client.get("/api/v1/queries")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 2
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `client` - FastAPI TestClient
- `mock_connection_manager` - Mocked Oracle connection manager
- `mock_query_fetcher` - Mocked QueryFetcher
- `sample_queries` - Sample query data

## Coverage Requirements

- Minimum coverage: **80%**
- Critical modules (connection, query_fetcher, query_service): **90%**

View coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Continuous Integration

Tests are automatically run on:
- Every pull request
- Every push to main branch
- Nightly builds

CI configuration: `.github/workflows/backend-tests.yml`

## Troubleshooting

### Tests fail with "ModuleNotFoundError"
Ensure you're in the backend directory and have installed dependencies:
```bash
cd backend
pip install -r requirements/test.txt
```

### Oracle connection tests fail
Oracle integration tests require a running Oracle database. Set environment variables:
```bash
export ORACLE_USER=test_user
export ORACLE_PASSWORD=test_password
export ORACLE_DSN=localhost:1521/XE
```

Or skip Oracle tests:
```bash
pytest -m "not oracle"
```

### Coverage is too low
Run coverage report to see uncovered lines:
```bash
pytest --cov=app --cov-report=term-missing
```

## Best Practices

1. **Test naming**: Use descriptive names that explain what is being tested
2. **Arrange-Act-Assert**: Structure tests clearly
3. **One assertion per test**: Keep tests focused
4. **Mock external dependencies**: Unit tests should be isolated
5. **Use fixtures**: Share common setup code
6. **Test edge cases**: Include error conditions and boundary values
7. **Keep tests fast**: Unit tests should complete in milliseconds
8. **Documentation**: Add docstrings to complex tests

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
