# API Design Standards

## Overview

This document defines REST API design principles and conventions for the Oracle Database Performance Tuning Tool backend API.

## General Principles

### RESTful Design
- Use HTTP methods correctly
- Resources are nouns, not verbs
- Stateless communication
- Use HTTP status codes appropriately

### Consistency
- Consistent naming across all endpoints
- Consistent response formats
- Consistent error handling

### Versioning
- API versioned via URL path: `/api/v1/...`
- Major version changes only for breaking changes
- Maintain backward compatibility when possible

## URL Structure

### Base URL
```
https://api.querytuner.example.com/api/v1
```

### Resource Naming
- **Use plural nouns** for collections
- **Lowercase with hyphens** for multi-word resources
- **Hierarchical structure** for nested resources

```
Good:
GET  /api/v1/queries
GET  /api/v1/queries/{sql_id}
GET  /api/v1/queries/{sql_id}/execution-plans
GET  /api/v1/execution-plans/{plan_id}/operations

Bad:
GET  /api/v1/getQueries
GET  /api/v1/query
GET  /api/v1/queries/{sql_id}/getExecutionPlans
```

### Query Parameters
- Use for filtering, sorting, pagination
- Use camelCase for parameter names
- Be consistent with parameter naming

```
GET /api/v1/queries?sortBy=elapsedTime&order=desc&page=1&pageSize=20
GET /api/v1/queries?minElapsedTime=1000&maxExecutions=100
GET /api/v1/wait-events?eventClass=User I/O&startTime=2024-01-01
```

## HTTP Methods

### GET - Retrieve Resources
- **Safe**: No side effects
- **Idempotent**: Multiple identical requests have same effect
- **Cacheable**: Response can be cached

```
GET /api/v1/queries              # List all queries
GET /api/v1/queries/{sql_id}     # Get specific query
GET /api/v1/queries/{sql_id}/execution-plans  # Get query plans
```

### POST - Create Resources
- **Not safe**: Has side effects
- **Not idempotent**: Multiple requests create multiple resources
- Returns created resource with `201 Created`

```
POST /api/v1/connections         # Create new database connection
POST /api/v1/queries/{sql_id}/analyze  # Trigger query analysis
```

### PUT - Update/Replace Resources
- **Not safe**: Has side effects
- **Idempotent**: Multiple identical requests have same effect
- Replace entire resource

```
PUT /api/v1/connections/{connection_id}  # Update connection details
```

### PATCH - Partial Update
- **Not safe**: Has side effects
- **May be idempotent**: Depends on implementation
- Update part of resource

```
PATCH /api/v1/queries/{sql_id}/metadata  # Update query metadata
```

### DELETE - Remove Resources
- **Not safe**: Has side effects
- **Idempotent**: Multiple identical requests have same effect

```
DELETE /api/v1/connections/{connection_id}
```

## Request Format

### Headers
```
Content-Type: application/json
Accept: application/json
Authorization: Bearer {jwt_token}
X-Request-ID: {unique_request_id}
```

### Request Body (JSON)
```json
{
  "host": "oracle-db.example.com",
  "port": 1521,
  "serviceName": "PROD",
  "username": "monitor_user"
}
```

### Request Validation
- Validate all inputs
- Return `400 Bad Request` for invalid data
- Provide detailed error messages

## Response Format

### Success Response Structure
```json
{
  "data": {
    "sqlId": "abc123xyz",
    "sqlText": "SELECT * FROM users WHERE id = :1",
    "elapsedTime": 1234.56,
    "executions": 100,
    "cpuTime": 987.65
  },
  "meta": {
    "timestamp": "2024-02-11T13:00:00Z",
    "requestId": "req-12345"
  }
}
```

### Collection Response with Pagination
```json
{
  "data": [
    {
      "sqlId": "abc123",
      "sqlText": "SELECT ...",
      "elapsedTime": 1000
    },
    {
      "sqlId": "def456",
      "sqlText": "UPDATE ...",
      "elapsedTime": 800
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalPages": 5,
    "totalItems": 95,
    "hasNext": true,
    "hasPrevious": false
  },
  "meta": {
    "timestamp": "2024-02-11T13:00:00Z",
    "requestId": "req-12346"
  }
}
```

### Error Response Structure
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
    "requestId": "req-12347",
    "path": "/api/v1/queries/abc123"
  }
}
```

## HTTP Status Codes

### Success Codes (2xx)
- **200 OK**: Successful GET, PUT, PATCH, or DELETE
- **201 Created**: Successful POST creating a resource
- **202 Accepted**: Request accepted for async processing
- **204 No Content**: Successful DELETE with no response body

### Client Error Codes (4xx)
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource not found
- **409 Conflict**: Request conflicts with current state
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded

### Server Error Codes (5xx)
- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Oracle database unavailable
- **503 Service Unavailable**: Service temporarily unavailable
- **504 Gateway Timeout**: Oracle database timeout

## Pagination

### Parameters
```
page: Page number (1-based)
pageSize: Items per page (default: 20, max: 100)
```

### Response
```
GET /api/v1/queries?page=2&pageSize=20
```

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "pageSize": 20,
    "totalPages": 5,
    "totalItems": 95,
    "hasNext": true,
    "hasPrevious": true,
    "links": {
      "self": "/api/v1/queries?page=2&pageSize=20",
      "first": "/api/v1/queries?page=1&pageSize=20",
      "prev": "/api/v1/queries?page=1&pageSize=20",
      "next": "/api/v1/queries?page=3&pageSize=20",
      "last": "/api/v1/queries?page=5&pageSize=20"
    }
  }
}
```

## Filtering

### Query Parameters
```
GET /api/v1/queries?minElapsedTime=1000&maxExecutions=100&schema=HR
```

### Complex Filters
```
GET /api/v1/queries?filter[elapsedTime][gte]=1000
GET /api/v1/queries?filter[schema][in]=HR,SALES
```

## Sorting

### Query Parameters
```
GET /api/v1/queries?sortBy=elapsedTime&order=desc
GET /api/v1/queries?sortBy=executions,elapsedTime&order=asc,desc
```

## Field Selection (Sparse Fieldsets)

Allow clients to request specific fields:

```
GET /api/v1/queries?fields=sqlId,sqlText,elapsedTime
GET /api/v1/queries/{sql_id}?fields=sqlText,executionPlan
```

## Error Handling

### Error Codes
Define application-specific error codes:

```
QUERY_NOT_FOUND
INVALID_SQL_ID
CONNECTION_FAILED
ORACLE_TIMEOUT
INSUFFICIENT_PRIVILEGES
INVALID_PARAMETERS
```

### Error Response
```json
{
  "error": {
    "code": "CONNECTION_FAILED",
    "message": "Failed to connect to Oracle database",
    "details": {
      "host": "oracle-db.example.com",
      "port": 1521,
      "serviceName": "PROD",
      "oracleError": "ORA-12541: TNS:no listener"
    },
    "timestamp": "2024-02-11T13:00:00Z",
    "requestId": "req-12348",
    "path": "/api/v1/connections/test"
  }
}
```

### Validation Errors
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
          "value": 99999
        },
        {
          "field": "username",
          "message": "Username is required",
          "value": null
        }
      ]
    },
    "timestamp": "2024-02-11T13:00:00Z",
    "requestId": "req-12349"
  }
}
```

## Authentication and Authorization

### Bearer Token Authentication
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Error Responses
```
401 Unauthorized - Missing or invalid token
403 Forbidden - Valid token but insufficient permissions
```

## Rate Limiting

### Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1640000000
```

### Error Response (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 1000,
      "window": "1 hour",
      "retryAfter": 3600
    }
  }
}
```

## Caching

### Cache-Control Headers
```
Cache-Control: public, max-age=30
Cache-Control: private, no-cache
Cache-Control: no-store
```

### ETag Support
```
Request:
GET /api/v1/queries/{sql_id}

Response:
200 OK
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"

Subsequent Request:
GET /api/v1/queries/{sql_id}
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"

Response if unchanged:
304 Not Modified
```

## Asynchronous Operations

For long-running operations:

### Initial Request
```
POST /api/v1/queries/{sql_id}/analyze
```

### Response
```
202 Accepted
Location: /api/v1/tasks/task-123

{
  "taskId": "task-123",
  "status": "pending",
  "statusUrl": "/api/v1/tasks/task-123"
}
```

### Check Status
```
GET /api/v1/tasks/task-123

{
  "taskId": "task-123",
  "status": "completed",
  "result": {
    "sqlId": "abc123",
    "recommendations": [...]
  }
}
```

## API Documentation

### OpenAPI/Swagger
- Auto-generate from FastAPI
- Available at `/api/v1/docs`
- Interactive documentation

### Endpoint Documentation Template
```
GET /api/v1/queries/{sql_id}

Summary: Get query details
Description: Retrieves detailed information for a specific SQL statement

Parameters:
  - sql_id (path, required): SQL_ID of the query (13 characters)
  - fields (query, optional): Comma-separated list of fields to return

Responses:
  200: Query details retrieved successfully
  404: Query not found
  500: Internal server error

Example Request:
  GET /api/v1/queries/abc123xyz?fields=sqlText,elapsedTime

Example Response:
  {
    "data": {
      "sqlId": "abc123xyz",
      "sqlText": "SELECT * FROM users",
      "elapsedTime": 1234.56
    }
  }
```

## Endpoint Examples

### Queries
```
GET    /api/v1/queries                       # List all queries
GET    /api/v1/queries/{sql_id}              # Get query details
GET    /api/v1/queries/{sql_id}/statistics   # Get query statistics
GET    /api/v1/queries/{sql_id}/execution-plans  # List execution plans
POST   /api/v1/queries/{sql_id}/analyze      # Analyze query
```

### Execution Plans
```
GET    /api/v1/execution-plans/{sql_id}     # Get current plan
GET    /api/v1/execution-plans/{sql_id}/history  # Get plan history
GET    /api/v1/execution-plans/{sql_id}/compare  # Compare plans
POST   /api/v1/execution-plans/{sql_id}/baseline  # Create plan baseline
```

### Wait Events
```
GET    /api/v1/wait-events                  # List wait events
GET    /api/v1/wait-events/{sql_id}         # Wait events for query
GET    /api/v1/wait-events/summary          # Wait event summary
```

### Recommendations
```
GET    /api/v1/recommendations/{sql_id}     # Get recommendations
POST   /api/v1/recommendations/{sql_id}/apply  # Apply recommendation
```

### Deadlocks
```
GET    /api/v1/deadlocks                    # List deadlocks
GET    /api/v1/deadlocks/{deadlock_id}      # Get deadlock details
```

### Statistics
```
GET    /api/v1/statistics/health            # Statistics health check
GET    /api/v1/statistics/stale             # List stale statistics
POST   /api/v1/statistics/gather            # Trigger statistics gathering
```

### Connections
```
GET    /api/v1/connections                  # List connections
POST   /api/v1/connections                  # Create connection
GET    /api/v1/connections/{id}             # Get connection
PUT    /api/v1/connections/{id}             # Update connection
DELETE /api/v1/connections/{id}             # Delete connection
POST   /api/v1/connections/{id}/test        # Test connection
```

### Users (Resource Usage)
```
GET    /api/v1/users                        # List database users
GET    /api/v1/users/{username}/resource-usage  # User resource usage
GET    /api/v1/users/{username}/sessions    # User sessions
```

## Versioning Strategy

### URL-based Versioning
```
/api/v1/queries
/api/v2/queries  # When breaking changes are introduced
```

### Version Lifecycle
- **v1**: Current stable version
- **v2-beta**: Beta version for testing
- **v1-deprecated**: Deprecated, will be removed in 6 months

### Breaking Changes
Changes that require a new API version:
- Removing endpoints
- Removing fields from responses
- Changing field types
- Changing URL structure
- Changing authentication mechanism

### Non-Breaking Changes
Can be made within same version:
- Adding new endpoints
- Adding new optional query parameters
- Adding new fields to responses
- Adding new HTTP headers
- Bug fixes

## Best Practices

1. **Use nouns for resources**, not verbs
2. **Be consistent** with naming and response formats
3. **Use proper HTTP methods** and status codes
4. **Provide pagination** for collections
5. **Support filtering and sorting**
6. **Version your API**
7. **Document thoroughly**
8. **Return appropriate error messages**
9. **Use HTTPS** in production
10. **Implement rate limiting**
11. **Cache when appropriate**
12. **Make APIs idempotent** when possible
13. **Keep URLs simple** and intuitive
14. **Use JSON** for request/response
15. **Validate input** strictly

## Resources

- [REST API Tutorial](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
