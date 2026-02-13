# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Coding standards documentation
- Development environment setup
- Project management documentation

## [0.1.0] - 2024-02-11

### Added
- Project initialization
- Git repository setup
- Complete folder structure for backend, frontend, deployment, docs, and standards
- Comprehensive coding standards:
  - Python style guide
  - TypeScript style guide
  - API design standards
  - Database standards
  - Testing standards
  - Git workflow
  - Code review checklist
  - Security standards
  - Naming conventions
  - Error handling standards
- Root-level documentation:
  - README.md
  - PROJECT_MANAGER.md
  - CHANGELOG.md (this file)
  - ROADMAP.md
  - SECURITY.md
  - LICENSE
- .gitignore for Python, Node.js, Docker, and IDE files
- .editorconfig for consistent editor configuration

### Development Setup
- Docker and Docker Compose configuration structure
- Backend Python project structure with FastAPI
- Frontend React + TypeScript project structure
- CI/CD pipeline structure with GitHub Actions

---

## Version History Template

For future releases, use this template:

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features and capabilities

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that have been removed

### Fixed
- Bug fixes

### Security
- Security-related changes and fixes

---

## Release Notes Guidelines

### Version Numbers
- **MAJOR** (X.0.0): Incompatible API changes, major new features
- **MINOR** (0.X.0): Backward-compatible new features
- **PATCH** (0.0.X): Backward-compatible bug fixes

### Entry Categories

#### Added
Use for new features, endpoints, components, or capabilities:
```
- feat(api): add execution plan comparison endpoint
- feat(frontend): add wait event visualization chart
- feat(backend): add deadlock detection module
```

#### Changed
Use for changes to existing functionality:
```
- refactor(backend): improve query caching strategy
- style(frontend): update query list UI design
- perf(api): optimize execution plan parsing
```

#### Deprecated
Use for features that will be removed in future versions:
```
- deprecate: V1 API endpoints (will be removed in v3.0.0)
- deprecate: Legacy connection format (use new format)
```

#### Removed
Use for features that have been removed:
```
- remove: V1 API endpoints (deprecated in v2.0.0)
- remove: Support for Oracle 10g
```

#### Fixed
Use for bug fixes:
```
- fix(backend): resolve connection pool leak
- fix(frontend): correct elapsed time formatting
- fix(api): handle null execution plans gracefully
```

#### Security
Use for security-related changes:
```
- security: update dependencies to patch CVE-2024-XXXX
- security: implement rate limiting on authentication endpoints
- security: add input validation for SQL_ID parameter
```

### Breaking Changes

Mark breaking changes clearly:
```
### Changed
- **BREAKING**: API response format changed from root-level data to `data` field
  - Migration: Update API clients to access `response.data` instead of `response`
  - See migration guide: docs/migrations/v2.0.0.md
```

### Example Release Entry

```markdown
## [1.2.0] - 2024-03-15

### Added
- feat(backend): add AWR/ASH integration for historical analysis (#123)
- feat(frontend): add plan comparison side-by-side view (#145)
- feat(api): add new endpoint GET /api/v1/recommendations/{sql_id} (#156)

### Changed
- perf(backend): improve query caching with Redis TTL optimization (#134)
- style(frontend): update dashboard with new color scheme (#142)

### Fixed
- fix(backend): resolve deadlock detection false positives (#138)
- fix(frontend): correct timezone handling in wait event timeline (#149)
- fix(api): handle missing execution plans gracefully (#151)

### Security
- security: update FastAPI to 0.104.1 to patch CVE-2024-12345 (#140)
```

---

[unreleased]: https://github.com/your-org/query-tuner-tool/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/query-tuner-tool/releases/tag/v0.1.0
