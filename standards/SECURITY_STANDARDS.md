# Security Standards

## Overview

This document defines security best practices, requirements, and guidelines for the Oracle Database Performance Tuning Tool.

## Security Principles

### Defense in Depth
- Multiple layers of security
- No single point of failure
- Assume breach mentality

### Least Privilege
- Minimum necessary permissions
- Separate monitoring from admin access
- Role-based access control

### Security by Default
- Secure defaults
- Opt-in for risky features
- Fail securely

## Authentication & Authorization

### User Authentication

#### JWT Tokens
```python
# Generate JWT token
from datetime import datetime, timedelta
import jwt

def create_access_token(user_id: str, expires_delta: timedelta = timedelta(hours=1)):
    """Create JWT access token."""
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Verify JWT token
def verify_token(token: str):
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
```

#### Password Security
- **Never store plain text passwords**
- **Use bcrypt or argon2** for hashing
- **Minimum length**: 12 characters
- **Enforce complexity**: Upper, lower, digit, special char

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed_password)
```

### Authorization

#### Role-Based Access Control (RBAC)
```python
from enum import Enum

class Role(Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

# Permission decorator
def require_role(required_role: Role):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if user.role != required_role:
                raise ForbiddenError("Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/api/v1/queries/{sql_id}")
@require_role(Role.ADMIN)
async def delete_query(sql_id: str):
    ...
```

## Database Security

### Oracle Connection Security

#### Never Hardcode Credentials
```python
# Bad - NEVER do this!
connection = cx_Oracle.connect("user/password@host:port/service")

# Good - Use environment variables
import os
connection = cx_Oracle.connect(
    user=os.getenv("ORACLE_USER"),
    password=os.getenv("ORACLE_PASSWORD"),
    dsn=os.getenv("ORACLE_DSN")
)
```

#### Use Oracle Wallet
```python
# Oracle Wallet for secure credential storage
connection = cx_Oracle.connect(dsn="/@tnsname", wallet_location="/path/to/wallet")
```

#### Dedicated Monitoring User
```sql
-- Create dedicated read-only monitoring user
CREATE USER query_monitor IDENTIFIED BY secure_password;

-- Grant only necessary privileges
GRANT CREATE SESSION TO query_monitor;
GRANT SELECT_CATALOG_ROLE TO query_monitor;

-- Grant specific object privileges
GRANT SELECT ON v_$sql TO query_monitor;
GRANT SELECT ON v_$session TO query_monitor;
-- DO NOT GRANT DML permissions
```

### SQL Injection Prevention

#### Always Use Bind Variables
```python
# VULNERABLE - SQL Injection Risk!
sql = f"SELECT * FROM v$sql WHERE sql_id = '{sql_id}'"
cursor.execute(sql)

# SECURE - Use bind variables
sql = "SELECT * FROM v$sql WHERE sql_id = :sql_id"
cursor.execute(sql, {"sql_id": sql_id})
```

#### Input Validation
```python
from pydantic import BaseModel, validator
import re

class QueryRequest(BaseModel):
    sql_id: str

    @validator('sql_id')
    def validate_sql_id(cls, v):
        # SQL_ID is exactly 13 alphanumeric characters
        if not re.match(r'^[a-zA-Z0-9]{13}$', v):
            raise ValueError('Invalid SQL_ID format')
        return v.upper()
```

### Connection Security

#### SSL/TLS for Database Connections
```python
# Configure Oracle Native Network Encryption
connection = cx_Oracle.connect(
    user=user,
    password=password,
    dsn=dsn,
    wallet_location="/path/to/wallet",
    wallet_password=wallet_password
)
```

#### Connection Pooling Security
```python
# Secure connection pool configuration
pool = cx_Oracle.SessionPool(
    user=user,
    password=password,
    dsn=dsn,
    min=5,
    max=20,
    timeout=300,  # Connection timeout
    wait_timeout=10000,  # Wait timeout
    max_lifetime_session=3600,  # Rotate connections
    session_callback=init_session  # Initialize security settings
)

def init_session(connection, requested_tag):
    """Initialize security settings for each connection."""
    cursor = connection.cursor()
    # Set session-level security
    cursor.execute("ALTER SESSION SET SQL_TRACE = FALSE")
    cursor.close()
```

## API Security

### Input Validation

#### Validate All Inputs
```python
from fastapi import HTTPException
from pydantic import BaseModel, Field, validator

class ConnectionRequest(BaseModel):
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    service_name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=128)

    @validator('host')
    def validate_host(cls, v):
        # Prevent SSRF attacks
        if v in ['localhost', '127.0.0.1', '0.0.0.0']:
            raise ValueError('Localhost connections not allowed')
        return v

    @validator('username')
    def validate_username(cls, v):
        # Alphanumeric and underscore only
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Invalid username format')
        return v
```

#### Sanitize Output
```python
import html

def sanitize_sql_text(sql_text: str) -> str:
    """Sanitize SQL text for display."""
    # Escape HTML to prevent XSS
    return html.escape(sql_text)
```

### HTTPS/TLS

#### Enforce HTTPS in Production
```python
# FastAPI configuration
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

#### Secure Headers
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)

# Secure session cookies
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=True,
    same_site="strict"
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Restrictive CORS policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600
)
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/queries")
@limiter.limit("100/hour")
async def get_queries(request: Request):
    ...
```

## Secrets Management

### Environment Variables

```python
# .env file (NEVER commit to git!)
ORACLE_USER=monitor_user
ORACLE_PASSWORD=secure_password
SECRET_KEY=your-secret-key-here
JWT_SECRET=jwt-secret-key-here

# Load environment variables
from pydantic import BaseSettings

class Settings(BaseSettings):
    oracle_user: str
    oracle_password: str
    secret_key: str
    jwt_secret: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### Secrets in Production

#### Use Secret Management Services
- **AWS Secrets Manager**
- **Azure Key Vault**
- **HashiCorp Vault**
- **Kubernetes Secrets**

```python
import boto3

def get_secret(secret_name):
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

### Rotate Secrets Regularly
- Database passwords: Every 90 days
- API keys: Every 90 days
- JWT secrets: Every 180 days

## Logging Security

### What to Log
- Authentication attempts (success/failure)
- Authorization failures
- API requests (sanitized)
- Error conditions
- Security events

### What NOT to Log
```python
# NEVER log sensitive data
logger.info(f"User {username} logged in with password {password}")  # BAD!

# NEVER log credentials
logger.debug(f"Connecting to Oracle: {connection_string}")  # BAD!

# NEVER log full credit card numbers, SSNs, passwords
```

### Secure Logging
```python
import logging

# Sanitize log messages
def sanitize_log(message: str) -> str:
    """Remove sensitive data from log messages."""
    # Remove passwords
    message = re.sub(r'password["\s=:]+[\w]+', 'password=***', message, flags=re.IGNORECASE)
    # Remove tokens
    message = re.sub(r'Bearer\s+[\w\-\.]+', 'Bearer ***', message)
    return message

logger.info(sanitize_log(f"Connection string: {conn_string}"))
```

## Error Handling Security

### Don't Leak Information in Errors

```python
# BAD - Leaks system information
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": traceback.format_exc()}
    )

# GOOD - Generic error message
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "requestId": request.state.request_id}
    )
```

### Custom Error Messages

```python
# Production error handler
if settings.environment == "production":
    error_message = "An error occurred"
else:
    error_message = str(exception)
```

## Dependency Security

### Keep Dependencies Updated

```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade package-name
```

### Pin Dependencies
```
# requirements.txt - Pin versions
fastapi==0.104.0
cx-Oracle==8.3.0
pydantic==2.4.2
```

### Scan for Vulnerabilities
```yaml
# GitHub Actions - Dependency scanning
- name: Run security scan
  uses: pypa/gh-action-pip-audit@v1.0.0
```

## Frontend Security

### XSS Prevention

```typescript
// Use React's built-in XSS protection
function QueryDisplay({ query }: { query: Query }) {
  // React automatically escapes text
  return <div>{query.sqlText}</div>;
}

// For HTML content, sanitize first
import DOMPurify from 'dompurify';

function HtmlContent({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

### CSRF Protection

```typescript
// Include CSRF token in requests
const response = await fetch('/api/v1/queries', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': getCsrfToken(),
  },
  body: JSON.stringify(data),
});
```

### Secure Storage

```typescript
// Use httpOnly cookies for tokens (backend sets)
// Don't store sensitive data in localStorage

// If you must use localStorage
const encryptData = (data: string): string => {
  // Use proper encryption library
  return CryptoJS.AES.encrypt(data, SECRET_KEY).toString();
};

const decryptData = (encrypted: string): string => {
  const bytes = CryptoJS.AES.decrypt(encrypted, SECRET_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
};
```

## Docker Security

### Secure Dockerfile

```dockerfile
# Use specific version, not 'latest'
FROM python:3.11.6-slim

# Don't run as root
RUN useradd -m -u 1000 appuser

# Copy only necessary files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose only necessary ports
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Scan Docker Images

```bash
# Scan for vulnerabilities
docker scan query-tuner-backend:latest

# Use Trivy
trivy image query-tuner-backend:latest
```

## Security Checklist

### Development
- [ ] No hardcoded secrets
- [ ] Input validation on all endpoints
- [ ] Bind variables for all SQL queries
- [ ] Proper error handling (don't leak info)
- [ ] Logging sanitized
- [ ] Dependencies up to date
- [ ] Security tests written

### Deployment
- [ ] HTTPS enforced
- [ ] Secure headers configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Secrets in secret manager
- [ ] Non-root Docker user
- [ ] Firewall rules configured
- [ ] Database user has minimum privileges

### Monitoring
- [ ] Log authentication failures
- [ ] Alert on suspicious activity
- [ ] Monitor rate limit violations
- [ ] Track failed authorization attempts
- [ ] Review access logs regularly

## Incident Response

### Security Incident Procedure

1. **Detect**: Monitor logs, alerts
2. **Contain**: Isolate affected systems
3. **Investigate**: Determine scope and impact
4. **Remediate**: Fix vulnerability
5. **Recover**: Restore normal operations
6. **Learn**: Post-mortem, update procedures

### Vulnerability Disclosure

**Reporting**: security@example.com
**Response Time**: 48 hours
**Fix Timeline**: 30 days for critical, 90 days for others

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
