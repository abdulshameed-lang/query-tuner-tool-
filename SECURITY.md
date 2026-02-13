# Security Policy

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities to:
- **Email**: security@example.com
- **Subject**: [SECURITY] Brief description of the vulnerability

### What to Include

Please include the following information in your report:
1. **Description**: Clear description of the vulnerability
2. **Impact**: Potential impact and severity
3. **Steps to Reproduce**: Detailed steps to reproduce the issue
4. **Proof of Concept**: Code or screenshots demonstrating the issue (if applicable)
5. **Suggested Fix**: Your recommendations for fixing the issue (optional)
6. **Your Contact Information**: So we can follow up with questions

### Example Report

```
Subject: [SECURITY] SQL Injection vulnerability in query endpoint

Description:
The GET /api/v1/queries endpoint is vulnerable to SQL injection through
the 'sortBy' query parameter.

Impact:
An attacker could potentially:
- Extract sensitive database information
- Modify or delete data
- Execute arbitrary SQL commands

Steps to Reproduce:
1. Send GET request to /api/v1/queries?sortBy=elapsed_time; DROP TABLE users--
2. Observe that the SQL injection is executed

Proof of Concept:
[Screenshots or code demonstrating the vulnerability]

Suggested Fix:
Validate and sanitize the sortBy parameter against a whitelist of allowed columns.

Contact: researcher@example.com
```

## Response Timeline

We are committed to responding to security reports promptly:

| Timeline | Action |
|----------|--------|
| **Within 48 hours** | Acknowledge receipt of your report |
| **Within 1 week** | Provide initial assessment and severity classification |
| **Within 30 days** | Release a fix for critical vulnerabilities |
| **Within 90 days** | Release a fix for non-critical vulnerabilities |

### Severity Classification

We use the following severity levels:

- **Critical**: Immediate risk of data breach, remote code execution
- **High**: Significant security impact, authentication bypass
- **Medium**: Security issue with limited impact
- **Low**: Minor security concerns

## Disclosure Policy

### Coordinated Disclosure

We follow a coordinated disclosure policy:

1. **Private Disclosure**: Report received and acknowledged
2. **Investigation**: We investigate and develop a fix
3. **Fix Development**: Patch is developed and tested
4. **Release**: Fix is released in a security update
5. **Public Disclosure**: Vulnerability is publicly disclosed 7 days after fix release
6. **Credit**: Reporter is credited (if desired)

### Public Disclosure

After a fix is released, we will:
- Publish a security advisory
- Update CHANGELOG.md with security fixes
- Credit the reporter (with permission)
- Provide details for users to update

## Security Best Practices for Users

### For Administrators

1. **Keep Software Updated**
   - Apply security updates promptly
   - Subscribe to security advisories
   - Monitor CHANGELOG.md for security fixes

2. **Secure Configuration**
   - Use strong passwords (minimum 12 characters)
   - Enable HTTPS/TLS for all connections
   - Use Oracle Wallet for database credentials
   - Restrict network access with firewalls

3. **Access Control**
   - Use principle of least privilege
   - Implement role-based access control
   - Regularly review user permissions
   - Disable unused accounts

4. **Monitoring**
   - Enable audit logging
   - Monitor for suspicious activity
   - Set up security alerts
   - Review logs regularly

5. **Oracle Database Security**
   - Use dedicated monitoring user with minimal privileges
   - Never use SYS or SYSTEM accounts
   - Enable Oracle audit logging
   - Use Oracle Native Network Encryption

### For Developers

1. **Secure Development**
   - Follow security standards (see [standards/SECURITY_STANDARDS.md](standards/SECURITY_STANDARDS.md))
   - Never hardcode credentials
   - Use bind variables for all SQL queries
   - Validate and sanitize all inputs

2. **Dependencies**
   - Keep dependencies updated
   - Use `safety` to scan for vulnerabilities
   - Review security advisories for dependencies
   - Use lock files (requirements.txt, package-lock.json)

3. **Code Review**
   - Security review for sensitive code
   - Use code review checklist
   - Never bypass security checks
   - Test for common vulnerabilities (OWASP Top 10)

4. **Testing**
   - Write security tests
   - Test authentication and authorization
   - Test input validation
   - Perform penetration testing before release

## Known Security Considerations

### Oracle Database Access

**Consideration**: The tool requires read access to Oracle system views (V$ and DBA_ views).

**Mitigation**:
- Use dedicated monitoring user with SELECT-only privileges
- Never grant DML permissions (INSERT, UPDATE, DELETE)
- Audit all database access
- Use connection pooling with timeouts

### API Authentication

**Consideration**: API endpoints expose database performance data.

**Mitigation**:
- JWT-based authentication required
- Rate limiting on all endpoints
- HTTPS required in production
- CORS properly configured

### Credential Storage

**Consideration**: Database credentials must be stored securely.

**Mitigation**:
- Never store credentials in code or version control
- Use environment variables or secret management services
- Encrypt credentials at rest
- Use Oracle Wallet when possible
- Rotate credentials regularly

### SQL Injection

**Consideration**: The tool queries Oracle system views with user input.

**Mitigation**:
- Always use bind variables
- Validate all inputs
- Whitelist allowed values where possible
- Never construct SQL with string concatenation

### Cross-Site Scripting (XSS)

**Consideration**: Query text and execution plans may contain special characters.

**Mitigation**:
- React automatically escapes output
- Sanitize HTML content with DOMPurify
- Use Content Security Policy headers
- Validate and sanitize all user inputs

### Denial of Service (DoS)

**Consideration**: Expensive queries could overload the database.

**Mitigation**:
- Query timeouts on all database operations
- Result set limits (pagination)
- Rate limiting on API endpoints
- Connection pool size limits
- Caching to reduce database load

## Security Features

### Current Security Features

- ✅ JWT-based authentication
- ✅ HTTPS/TLS support
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (bind variables)
- ✅ XSS prevention (React escaping)
- ✅ CORS configuration
- ✅ Rate limiting
- ✅ Secure password hashing (bcrypt)
- ✅ Oracle Wallet support
- ✅ Security headers (X-Content-Type-Options, X-Frame-Options, etc.)

### Planned Security Features

- [ ] Two-factor authentication (2FA)
- [ ] Single sign-on (SSO) integration
- [ ] IP whitelisting
- [ ] Advanced audit logging
- [ ] Intrusion detection
- [ ] Automated vulnerability scanning
- [ ] Security compliance reports

## Security Updates

### Supported Versions

We provide security updates for:

| Version | Supported |
|---------|-----------|
| 1.x.x   | ✅ Yes    |
| 0.x.x   | ⚠️ Development only |

### Update Notifications

Subscribe to security updates:
- **GitHub**: Watch repository for security advisories
- **Email**: Subscribe to security mailing list (coming soon)
- **RSS**: Security advisory RSS feed (coming soon)

## Compliance

### Standards and Frameworks

We align with industry security standards:
- **OWASP Top 10**: Web application security risks
- **CWE Top 25**: Common software weaknesses
- **NIST Cybersecurity Framework**: Security controls
- **ISO 27001**: Information security management

### Data Privacy

We are committed to protecting user data:
- No storage of sensitive query data (unless explicitly configured)
- PII masking in logs and outputs
- Data encryption at rest and in transit
- Regular security assessments

## Security Contacts

- **Security Issues**: security@example.com
- **General Security Questions**: security@example.com
- **Security Team**: [Security team members]

## Acknowledgments

We thank the following security researchers for responsibly disclosing vulnerabilities:

- [Name] - [Vulnerability] - [Date]
- [More acknowledgments as they occur]

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Oracle Security Best Practices](https://www.oracle.com/security/database-security/)

---

**Last Updated**: 2024-02-11
**Next Review**: Quarterly
