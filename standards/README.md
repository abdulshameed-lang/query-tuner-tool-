# Coding Standards and Conventions

## Overview

This directory contains coding standards and conventions for the Oracle Database Performance Tuning Tool project. These standards ensure code quality, maintainability, and consistency across the codebase.

## Purpose

- **Consistency**: Maintain uniform code style across the project
- **Quality**: Ensure high-quality, maintainable code
- **Collaboration**: Make code reviews more efficient
- **Onboarding**: Help new team members quickly understand project conventions

## Standards Documents

### Language-Specific Standards
- **[PYTHON_STYLE_GUIDE.md](./PYTHON_STYLE_GUIDE.md)** - Python coding standards for backend development
- **[TYPESCRIPT_STYLE_GUIDE.md](./TYPESCRIPT_STYLE_GUIDE.md)** - TypeScript/React coding standards for frontend development

### Design and Architecture Standards
- **[API_DESIGN_STANDARDS.md](./API_DESIGN_STANDARDS.md)** - REST API design principles and conventions
- **[DATABASE_STANDARDS.md](./DATABASE_STANDARDS.md)** - Oracle database query and optimization standards

### Quality Assurance Standards
- **[TESTING_STANDARDS.md](./TESTING_STANDARDS.md)** - Testing conventions and coverage requirements
- **[SECURITY_STANDARDS.md](./SECURITY_STANDARDS.md)** - Security best practices and requirements
- **[ERROR_HANDLING.md](./ERROR_HANDLING.md)** - Error handling patterns and practices

### Development Workflow Standards
- **[GIT_WORKFLOW.md](./GIT_WORKFLOW.md)** - Git branching strategy and commit conventions
- **[CODE_REVIEW_CHECKLIST.md](./CODE_REVIEW_CHECKLIST.md)** - Code review guidelines and checklist
- **[NAMING_CONVENTIONS.md](./NAMING_CONVENTIONS.md)** - Naming conventions for files, variables, and functions

## Enforcement Mechanisms

### Automated Enforcement

We use the following tools to automatically enforce coding standards:

#### Backend (Python)
- **Black**: Code formatting (line length: 88)
- **isort**: Import statement ordering
- **flake8**: Linting and style checking
- **mypy**: Static type checking
- **pylint**: Additional code quality checks

#### Frontend (TypeScript/React)
- **ESLint**: Linting and code quality
- **Prettier**: Code formatting
- **TypeScript Compiler**: Type checking in strict mode

### Pre-commit Hooks

Pre-commit hooks automatically run checks before commits:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### CI/CD Pipeline

GitHub Actions runs automated checks on all pull requests:
- Linting and formatting checks
- Type checking
- Unit and integration tests
- Code coverage analysis
- Security vulnerability scanning

## How to Use These Standards

### For Developers

1. **Before Starting**: Read all relevant standards documents
2. **During Development**: Reference standards when in doubt
3. **Before Committing**: Run linters and formatters
4. **During Code Review**: Use the code review checklist

### For Code Reviewers

1. Use [CODE_REVIEW_CHECKLIST.md](./CODE_REVIEW_CHECKLIST.md) as a guide
2. Focus on logic and architecture in reviews
3. Let automated tools catch style issues
4. Provide constructive feedback

### For New Team Members

1. Read this README first
2. Set up your development environment with linters/formatters
3. Review language-specific style guides for your work area
4. Ask questions in code reviews to learn project conventions

## Updating Standards

Standards should evolve with the project:

- **Propose Changes**: Submit a pull request with rationale
- **Discuss**: Team discussion before adoption
- **Document**: Update relevant documentation
- **Communicate**: Announce changes to the team

## Getting Help

If you have questions about coding standards:

1. Check the relevant standards document
2. Review similar code in the codebase
3. Ask in code reviews
4. Propose clarifications to standards documents

## Standard Priorities

When standards conflict or are unclear:

1. **Security** > Style
2. **Correctness** > Performance > Style
3. **Readability** > Cleverness
4. **Explicit** > Implicit
5. **Simple** > Complex

## Tools Setup

### Python Development

```bash
# Install development dependencies
pip install -r backend/requirements/dev.txt

# Format code
black backend/

# Sort imports
isort backend/

# Lint code
flake8 backend/
pylint backend/app/

# Type check
mypy backend/app/
```

### TypeScript/React Development

```bash
# Install dependencies
cd frontend && npm install

# Lint and fix
npm run lint
npm run lint:fix

# Format code
npm run format

# Type check
npm run type-check
```

## Exemptions

In rare cases, you may need to deviate from standards:

- **Document Why**: Add comments explaining the deviation
- **Limit Scope**: Keep deviations minimal and localized
- **Review Carefully**: Require extra scrutiny in code review

Example:
```python
# Disabling pylint check because external API requires this format
# pylint: disable=invalid-name
externalApiRequiredName = get_external_data()
```

## Resources

- [PEP 8 - Python Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

## Continuous Improvement

We encourage feedback on these standards:

- Are they clear and easy to follow?
- Are they enforced consistently?
- Do they improve code quality?
- Are there gaps or conflicts?

Submit issues or pull requests to improve our standards.
