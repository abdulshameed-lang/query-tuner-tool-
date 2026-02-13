# Code Review Checklist

## Overview

This checklist guides code reviewers to ensure consistent, high-quality code reviews for the Oracle Database Performance Tuning Tool.

## General Principles

### Code Review Goals
- **Ensure correctness**: Code works as intended
- **Improve quality**: Code is readable and maintainable
- **Share knowledge**: Learn from each other
- **Catch bugs early**: Before they reach production
- **Enforce standards**: Maintain consistency

### Reviewer Mindset
- **Be respectful**: Constructive, not critical
- **Be thorough**: Don't rush reviews
- **Be helpful**: Suggest improvements, not just problems
- **Be open**: Consider author's perspective
- **Be timely**: Review within 24 hours

## Pre-Review Checks

Before starting review, verify:

- [ ] **CI/CD passes**: All automated checks green
- [ ] **Tests pass**: Unit, integration, E2E tests
- [ ] **Coverage meets requirements**: ≥80% overall
- [ ] **No linting errors**: Clean linter output
- [ ] **PR description complete**: Clear explanation of changes
- [ ] **Related issues linked**: Proper issue references

## Code Quality Checklist

### 1. Functionality

- [ ] **Meets requirements**: Addresses issue/feature completely
- [ ] **Logic is correct**: Algorithm/logic works as intended
- [ ] **Edge cases handled**: Boundary conditions considered
- [ ] **Error cases handled**: Failures handled gracefully
- [ ] **No obvious bugs**: Code doesn't have apparent issues

### 2. Code Design

- [ ] **Single Responsibility**: Functions/classes do one thing well
- [ ] **DRY principle**: No unnecessary code duplication
- [ ] **SOLID principles**: Good object-oriented design
- [ ] **Appropriate abstractions**: Right level of abstraction
- [ ] **No over-engineering**: Simple solution to problem
- [ ] **Separation of concerns**: Logic properly separated

### 3. Readability

- [ ] **Clear naming**: Variables/functions have meaningful names
- [ ] **Appropriate comments**: Complex logic explained
- [ ] **No commented code**: Removed or properly explained
- [ ] **Consistent style**: Follows project style guide
- [ ] **Easy to understand**: Code is self-documenting
- [ ] **Proper formatting**: Clean, consistent formatting

### 4. Performance

- [ ] **No obvious bottlenecks**: No performance anti-patterns
- [ ] **Efficient algorithms**: Appropriate algorithm choice
- [ ] **Resource management**: Memory/connections properly managed
- [ ] **Database queries optimized**: Efficient SQL queries
- [ ] **Caching appropriate**: Caching used where beneficial
- [ ] **No premature optimization**: Optimize only when needed

### 5. Security

- [ ] **Input validation**: All inputs validated
- [ ] **SQL injection prevention**: Bind variables used
- [ ] **XSS prevention**: Output properly escaped
- [ ] **Authentication checked**: Auth required where needed
- [ ] **Authorization checked**: Permissions verified
- [ ] **No secrets in code**: Credentials not hardcoded
- [ ] **Secure dependencies**: No vulnerable packages

### 6. Testing

- [ ] **Tests added**: New functionality has tests
- [ ] **Tests are meaningful**: Tests actually validate behavior
- [ ] **Edge cases tested**: Boundary conditions covered
- [ ] **Error cases tested**: Failure scenarios covered
- [ ] **Tests pass**: All tests green
- [ ] **Test names clear**: Descriptive test names
- [ ] **No flaky tests**: Tests are reliable

### 7. Documentation

- [ ] **Public APIs documented**: Functions have docstrings
- [ ] **Complex logic explained**: Comments where needed
- [ ] **README updated**: If user-facing changes
- [ ] **API docs updated**: If API changes
- [ ] **Changelog updated**: Notable changes documented
- [ ] **Migration guide**: If breaking changes

## Language-Specific Checks

### Python (Backend)

- [ ] **Type hints present**: All function signatures typed
- [ ] **Docstrings present**: Public functions documented
- [ ] **PEP 8 compliant**: Follows Python style guide
- [ ] **No mutable defaults**: No `def func(arg=[])`
- [ ] **Context managers used**: For resources (files, connections)
- [ ] **Exceptions specific**: Not catching generic `Exception`
- [ ] **Async used correctly**: Proper async/await usage

### TypeScript/React (Frontend)

- [ ] **Types defined**: No `any` types
- [ ] **Props typed**: Component props have interfaces
- [ ] **Hooks used correctly**: Following Rules of Hooks
- [ ] **Effects have deps**: useEffect dependencies correct
- [ ] **Keys on lists**: Proper key props on list items
- [ ] **No inline functions**: In JSX (performance)
- [ ] **Accessibility**: ARIA labels, semantic HTML

### SQL/Oracle

- [ ] **Bind variables used**: No string concatenation
- [ ] **Efficient queries**: Proper indexes, no full scans
- [ ] **Result sets limited**: FETCH FIRST or WHERE rownum
- [ ] **Read-only**: No INSERT/UPDATE/DELETE
- [ ] **Connection cleanup**: Cursors/connections closed

## API-Specific Checks

- [ ] **RESTful design**: Follows REST principles
- [ ] **Proper HTTP methods**: GET/POST/PUT/DELETE used correctly
- [ ] **Status codes correct**: 200, 201, 400, 404, 500 appropriate
- [ ] **Request validation**: Input validated before processing
- [ ] **Response format consistent**: Follows API standards
- [ ] **Error responses clear**: Meaningful error messages
- [ ] **Pagination implemented**: For collection endpoints
- [ ] **Versioned**: API version in URL if needed

## Architecture Checks

- [ ] **Layer separation**: Proper separation (API, service, data)
- [ ] **Dependencies correct**: Proper dependency direction
- [ ] **No circular dependencies**: Clean dependency graph
- [ ] **Interfaces defined**: Clear contracts between layers
- [ ] **Testable design**: Code is easy to test
- [ ] **Configuration externalized**: No hardcoded config

## Database Checks

- [ ] **Migrations present**: If schema changes
- [ ] **Migrations reversible**: Down migrations work
- [ ] **No data loss**: Migrations preserve data
- [ ] **Indexes added**: If new columns queried
- [ ] **Constraints appropriate**: Foreign keys, unique, not null

## Deployment Checks

- [ ] **Environment variables**: Used for config
- [ ] **Secrets not committed**: No passwords in code
- [ ] **Docker builds**: Dockerfile works if changed
- [ ] **Dependencies updated**: package.json/requirements.txt updated
- [ ] **Breaking changes noted**: If API/behavior changes

## Review Comments

### Types of Comments

1. **Blocking**: Must be addressed before merge
   - Security issues
   - Bugs
   - Breaking changes without migration
   - Missing tests for critical features

2. **Non-blocking**: Should be addressed but not blocking
   - Style improvements
   - Refactoring suggestions
   - Performance optimizations
   - Documentation improvements

3. **Nitpicks**: Minor suggestions
   - Naming improvements
   - Formatting tweaks
   - Comment additions

### Writing Good Comments

#### Do:
```
Consider using a dictionary here instead of multiple if statements.
This would make adding new types easier in the future.

Suggested:
type_handlers = {
    'query': handle_query,
    'plan': handle_plan,
}
return type_handlers.get(type, handle_default)()
```

#### Don't:
```
This is wrong. Fix it.
```

### Comment Templates

**Bug/Issue**:
```
🐛 This will fail when user is None.
Add a null check before accessing user.username.
```

**Security**:
```
🔒 Security: This is vulnerable to SQL injection.
Use bind variables instead of string formatting.
```

**Performance**:
```
⚡ Performance: This query could be slow with large datasets.
Consider adding pagination or a LIMIT clause.
```

**Suggestion**:
```
💡 Suggestion: Consider extracting this into a separate function
for better testability and reusability.
```

**Question**:
```
❓ Question: Why are we using a list here instead of a set?
Won't there be duplicates?
```

**Nitpick**:
```
🎨 Nitpick: This variable name could be more descriptive.
Perhaps `elapsed_time_ms` instead of `time`?
```

## Approval Guidelines

### Approve When:
- All blocking issues addressed
- Code meets quality standards
- Tests are comprehensive
- Documentation is complete
- You understand the changes
- You would maintain this code

### Request Changes When:
- Blocking issues present
- Tests missing or inadequate
- Security vulnerabilities exist
- Breaking changes without migration
- Code doesn't meet standards

### Comment (No Approval) When:
- Only non-blocking suggestions
- Questions for clarification
- FYI information for author

## After Approval

- [ ] **Squash commits**: If multiple commits need cleanup
- [ ] **Update CHANGELOG**: If user-facing changes
- [ ] **Update documentation**: If needed
- [ ] **Deploy plan**: Consider deployment timing
- [ ] **Monitor**: Watch for issues after merge

## Review Time Guidelines

### Response Time
- **Small PRs (<100 lines)**: Within 4 hours
- **Medium PRs (100-500 lines)**: Within 24 hours
- **Large PRs (>500 lines)**: Within 48 hours

### Review Duration
- **Small PRs**: 10-15 minutes
- **Medium PRs**: 30-60 minutes
- **Large PRs**: 1-2 hours (or request split)

## Large PR Guidelines

If PR is too large (>500 lines):
- **Request split**: Ask author to break into smaller PRs
- **Prioritize critical sections**: Focus on high-risk code
- **Multiple reviewers**: Get additional reviews
- **Schedule time**: Block calendar time for review

## Conflict Resolution

If author disagrees with feedback:
1. **Discuss**: Have synchronous discussion
2. **Explain rationale**: Both sides explain reasoning
3. **Escalate if needed**: Bring in tech lead
4. **Document decision**: Record outcome for future reference

## Best Practices

### For Reviewers
1. **Review promptly**: Don't block progress
2. **Be thorough**: Don't rush
3. **Focus on important**: Don't nitpick excessively
4. **Explain why**: Not just what to change
5. **Suggest solutions**: Don't just point out problems
6. **Appreciate good work**: Compliment good code
7. **Learn**: Every review is learning opportunity

### For Authors
1. **Self-review first**: Review own PR before requesting review
2. **Keep PRs small**: Easier to review
3. **Write good descriptions**: Help reviewer understand
4. **Respond promptly**: Address feedback quickly
5. **Ask questions**: If feedback unclear
6. **Don't take personally**: Feedback is about code, not you
7. **Thank reviewers**: Appreciate their time

## Resources

- [Google Code Review Guidelines](https://google.github.io/eng-practices/review/)
- [Conventional Comments](https://conventionalcomments.org/)
- [How to Review Code Effectively](https://github.com/thoughtbot/guides/tree/main/code-review)
