# Git Workflow

## Overview

This document defines Git branching strategy, commit conventions, and pull request process for the Oracle Database Performance Tuning Tool.

## Branching Strategy

We use **Git Flow** with the following branches:

### Main Branches
- **`main`**: Production-ready code, always stable
- **`develop`**: Integration branch for features, next release

### Supporting Branches
- **`feature/*`**: New features
- **`bugfix/*`**: Bug fixes
- **`hotfix/*`**: Urgent production fixes
- **`release/*`**: Release preparation

## Branch Naming Conventions

### Feature Branches
```
feature/short-description
feature/add-execution-plan-visualization
feature/implement-deadlock-detection
```

### Bugfix Branches
```
bugfix/short-description
bugfix/fix-connection-pool-leak
bugfix/correct-elapsed-time-calculation
```

### Hotfix Branches
```
hotfix/short-description
hotfix/fix-critical-sql-injection
hotfix/patch-oracle-connection-crash
```

### Release Branches
```
release/v1.0.0
release/v1.1.0
```

## Branch Workflow

### Creating a Feature Branch

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/add-wait-event-analysis

# Work on feature
git add .
git commit -m "feat: add wait event data model"

# Push to remote
git push -u origin feature/add-wait-event-analysis
```

### Merging Feature to Develop

```bash
# Update feature branch with latest develop
git checkout feature/add-wait-event-analysis
git pull origin develop
git merge develop

# Resolve conflicts if any
# Run tests
pytest backend/tests
npm test --prefix frontend

# Push and create pull request
git push origin feature/add-wait-event-analysis
```

### Creating a Release

```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0

# Update version numbers, changelog
# Commit changes
git commit -m "chore: prepare v1.0.0 release"

# Merge to main
git checkout main
git merge release/v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge release/v1.0.0
git push origin develop

# Delete release branch
git branch -d release/v1.0.0
```

### Hotfix Process

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/fix-critical-bug

# Fix the bug
git add .
git commit -m "fix: resolve critical connection issue"

# Merge to main
git checkout main
git merge hotfix/fix-critical-bug
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin main --tags

# Merge to develop
git checkout develop
git merge hotfix/fix-critical-bug
git push origin develop

# Delete hotfix branch
git branch -d hotfix/fix-critical-bug
```

## Commit Message Convention

We follow **Conventional Commits** specification.

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring (no feature or bug fix)
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Build process, dependencies, tooling
- **ci**: CI/CD pipeline changes

### Scope (Optional)
- **backend**: Backend changes
- **frontend**: Frontend changes
- **api**: API changes
- **db**: Database-related changes
- **docker**: Docker configuration
- **docs**: Documentation

### Examples

```bash
# Feature
feat(backend): add execution plan comparison endpoint

Implements GET /api/v1/execution-plans/{sql_id}/compare
to compare current and historical execution plans.

Closes #123

# Bug fix
fix(frontend): correct elapsed time formatting

Fixed issue where elapsed time was displayed in microseconds
instead of milliseconds for values under 1 second.

Fixes #456

# Documentation
docs: update API reference for query endpoints

Added examples for filtering and pagination parameters.

# Refactoring
refactor(backend): extract query parsing into separate module

Moved SQL parsing logic from query_analyzer.py to new
sql_parser.py module for better separation of concerns.

# Performance
perf(backend): optimize connection pool initialization

Reduced initial connection creation from 20 to 5 connections,
improving startup time by 50%.

# Test
test(backend): add integration tests for Oracle connection

Added tests covering connection pool lifecycle, error handling,
and timeout scenarios.

# Chore
chore(deps): update fastapi to 0.104.0

Updated FastAPI and related dependencies to latest versions.
```

### Commit Message Best Practices

1. **Use imperative mood**: "add feature" not "added feature"
2. **Capitalize subject**: Start with capital letter
3. **No period at end**: Don't end subject with period
4. **Limit subject to 50 characters**: Keep it concise
5. **Separate subject from body**: Blank line between them
6. **Wrap body at 72 characters**: For readability
7. **Explain what and why**: Not how (code shows how)
8. **Reference issues**: Link to issue numbers

### Bad Examples

```bash
# Too vague
git commit -m "fix bug"

# Not imperative
git commit -m "Fixed the connection issue"

# No type
git commit -m "Add new feature for queries"

# Too long subject
git commit -m "feat: add execution plan visualization with interactive tree and cost analysis and highlighting of expensive operations"
```

### Good Examples

```bash
# Clear and concise
git commit -m "feat(api): add query filtering by elapsed time"

# With body
git commit -m "fix(backend): prevent connection pool exhaustion

Added connection timeout and maximum wait time to prevent
indefinite blocking when pool is exhausted.

Fixes #789"

# Breaking change
git commit -m "feat(api): change query response format

BREAKING CHANGE: Query response now returns data in 'data'
field instead of root level. Update API clients accordingly.

Migration guide: https://docs.example.com/migration/v2
```

## Pull Request Process

### Creating a Pull Request

1. **Update branch** with latest develop/main
2. **Run all tests** and ensure they pass
3. **Run linters** and fix issues
4. **Write descriptive title** (like commit message)
5. **Fill PR template** completely
6. **Request reviewers**
7. **Link related issues**

### PR Title Format

Same as commit message:
```
feat(backend): add deadlock detection module
fix(frontend): correct query list pagination
docs: update deployment guide
```

### PR Description Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Changes Made
- Added deadlock detection module
- Implemented alert log parsing
- Created deadlock graph visualization
- Added tests for deadlock detection

## Related Issues
Closes #123
Related to #456

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests passing

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added that prove fix/feature works
- [ ] Dependent changes merged
```

### Code Review Requirements

**Minimum Reviews**: 1 approval required

**Required Checks**:
- [ ] All CI/CD tests pass
- [ ] Code coverage meets requirements
- [ ] No linting errors
- [ ] No security vulnerabilities

### Review Process

1. **Reviewer checks** code quality, logic, tests
2. **Reviewer comments** on issues or suggestions
3. **Author addresses** feedback
4. **Reviewer approves** once satisfied
5. **Author merges** PR

### Merge Strategy

- **Squash and merge**: For feature branches (keeps main/develop clean)
- **Merge commit**: For release/hotfix branches (preserves history)
- **Rebase and merge**: Not recommended (can cause issues)

## Git Best Practices

### Do's

1. **Commit often**: Small, logical commits
2. **Write good messages**: Clear and descriptive
3. **Pull before push**: Avoid conflicts
4. **Keep branches short-lived**: Merge within 1-2 weeks
5. **Delete merged branches**: Clean up after merge
6. **Use .gitignore**: Don't commit generated files
7. **Review before committing**: Check `git diff`
8. **Test before pushing**: Ensure code works

### Don'ts

1. **Don't commit secrets**: No passwords, API keys
2. **Don't commit large files**: Use Git LFS if needed
3. **Don't force push**: To shared branches (main, develop)
4. **Don't mix concerns**: One feature per branch
5. **Don't commit commented code**: Remove or delete
6. **Don't commit directly to main**: Always use PRs
7. **Don't rewrite published history**: On shared branches

## Common Git Commands

### Branch Management

```bash
# List all branches
git branch -a

# Create and switch to new branch
git checkout -b feature/new-feature

# Switch branch
git checkout develop

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature

# Rename branch
git branch -m old-name new-name
```

### Syncing with Remote

```bash
# Fetch updates
git fetch origin

# Pull updates
git pull origin develop

# Push changes
git push origin feature/my-feature

# Push with upstream tracking
git push -u origin feature/my-feature
```

### Stashing Changes

```bash
# Stash changes
git stash

# Stash with message
git stash save "WIP: working on feature"

# List stashes
git stash list

# Apply latest stash
git stash apply

# Apply and remove stash
git stash pop

# Drop stash
git stash drop
```

### Viewing History

```bash
# View commit history
git log

# View compact history
git log --oneline

# View history with graph
git log --graph --oneline --all

# View changes in commit
git show <commit-hash>

# View file history
git log -p -- path/to/file
```

### Undoing Changes

```bash
# Discard uncommitted changes (CAREFUL!)
git restore path/to/file

# Unstage file
git restore --staged path/to/file

# Amend last commit (if not pushed)
git commit --amend

# Revert commit (creates new commit)
git revert <commit-hash>

# Reset to previous commit (CAREFUL!)
git reset --hard HEAD~1
```

## Handling Merge Conflicts

### Resolving Conflicts

```bash
# Pull latest changes
git pull origin develop

# If conflicts occur:
# 1. Open conflicted files
# 2. Look for conflict markers:
#    <<<<<<< HEAD
#    Your changes
#    =======
#    Their changes
#    >>>>>>> branch-name

# 3. Resolve conflicts by editing files
# 4. Remove conflict markers
# 5. Stage resolved files
git add path/to/resolved/file

# 6. Complete merge
git commit

# 7. Push changes
git push
```

### Merge Strategies

```bash
# Prefer ours (keep our changes)
git merge -X ours develop

# Prefer theirs (keep their changes)
git merge -X theirs develop

# Abort merge
git merge --abort
```

## Git Hooks

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Run linters
echo "Running linters..."
black backend/ --check
isort backend/ --check
flake8 backend/

# Run tests
echo "Running tests..."
pytest backend/tests/unit

# If any command fails, prevent commit
if [ $? -ne 0 ]; then
    echo "Pre-commit checks failed!"
    exit 1
fi
```

### Using Pre-commit Framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

## Semantic Versioning

We follow **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

### Examples

- `1.0.0`: Initial release
- `1.1.0`: Added new feature (wait event analysis)
- `1.1.1`: Bug fix (connection pool leak)
- `2.0.0`: Breaking change (new API format)

### Tagging Releases

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tags
git push origin --tags

# List tags
git tag -l

# Delete tag locally
git tag -d v1.0.0

# Delete tag remotely
git push origin --delete v1.0.0
```

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
