---
description: Initialize coding standards for this project. Sets conventions for Django/DRF using agent-os/standards/.
---

# /init-standards

## Rules
- Run once per project (or when standards need updating)
- Creates/updates standards docs in `agent-os/standards/`
- Interview user for preferences if not specified

---

## Steps

### 1. Check Existing Standards

Check if `agent-os/standards/` already exists with structure:
```
agent-os/standards/
├── backend/
│   ├── api.md
│   ├── migrations.md
│   ├── models.md
│   └── python-django.md
├── frontend/
│   ├── accessibility.md
│   ├── components.md
│   └── css.md
├── global/
│   ├── coding-style.md
│   ├── commenting.md
│   ├── conventions.md
│   ├── error-handling.md
│   ├── tech-stack.md
│   └── validation.md
├── testing/
│   └── test-writing.md
└── index.yml
```

If exists, ask: "Standards exist. Update specific sections? Or full refresh?"

---

### 2. Interview for Preferences (if not already defined)

**General:**
- Line length: 88, 100, 120?
- Any existing linters/formatters in use?

**Python (Django):**
- Indentation: spaces (4)?
- Quotes: single or double?
- Docstring style: Google, NumPy, Sphinx?
- Type hints: strict or optional?

---

### 3. Create/Update Standards Structure

#### 3.1 Create `agent-os/standards/index.yml`

```yaml
# Agent OS Standards Index

backend:
  api:
    description: REST API design patterns and conventions
  migrations:
    description: Database migration best practices
  models:
    description: Django model patterns and conventions
  python-django:
    description: Python and Django coding standards

frontend:
  accessibility:
    description: Accessibility (a11y) requirements
  components:
    description: Component architecture patterns
  css:
    description: CSS/styling conventions

global:
  coding-style:
    description: General code style across all languages
  commenting:
    description: Code documentation standards
  conventions:
    description: Naming and structural conventions
  error-handling:
    description: Error handling patterns
  tech-stack:
    description: Technology stack decisions
  validation:
    description: Input validation patterns

testing:
  test-writing:
    description: Test writing patterns and coverage requirements
```

#### 3.2 `agent-os/standards/global/coding-style.md`

```markdown
# General Coding Standards

## All Languages
- Max line length: [88/100/120]
- Use meaningful variable names
- Prefer explicit over implicit
- Comment "why" not "what"

## Error Handling
- Always handle errors explicitly
- Log errors with context
- Use custom exceptions where appropriate

## Logging
- Use structured logging
- Include request IDs for tracing
- Log levels: DEBUG, INFO, WARNING, ERROR
```

#### 3.3 `agent-os/standards/backend/python-django.md`

```markdown
# Django Standards

## Models
- Add `__str__` method to all models
- Use `related_name` for ForeignKey/M2M

## Views/APIs
- Use DRF ViewSets for CRUD
- Filter querysets by user for IDOR protection

## Celery Tasks
- Naming: `apps.{app}.tasks.{task_name}`
- Use `@shared_task` decorator
- Handle retries explicitly
```

#### 3.4 `agent-os/standards/backend/api.md`

```markdown
# API Standards

## REST Conventions
- Use plural nouns for resources
- Use HTTP methods correctly (GET, POST, PUT, PATCH, DELETE)
- Return appropriate status codes

## Authentication
- JWT for user authentication
- API keys for service-to-service

## Response Format
- Use consistent response structure
- Include pagination for lists

## Error Responses
- Include error code and message
- Provide helpful error details in development
```

#### 3.5 `agent-os/standards/testing/test-writing.md`

```markdown
# Testing Standards

## Django Tests
- Location: `apps/<app>/tests/`
- Use `TestCase` for DB tests
- Use fixtures for test data
- Run: `docker compose exec be python manage.py test`

## E2E Tests
- Location: `tests/e2e/`
- Test full user flows
- Run against Docker environment
```

#### 3.6 `agent-os/standards/global/conventions.md`

```markdown
# Conventions

## Branch Naming
- Features: `feature/<slug>`
- Bugfixes: `bugfix/<slug>`
- Refactors: `refactor/<slug>`

## Commit Messages
- Features: `feat(<slug>): <description>`
- Bugfixes: `fix(<slug>): <description>`
- Refactors: `refactor(<slug>): <description>`
- Chores: `chore: <description>`

## Spec Organization
- Location: `agent-os/specs/<YYYY-MM-DD>-<slug>/`
- Contains: spec.md, tasks.md, planning/

## PR Guidelines
- Link to spec
- Include test plan
- Tag reviewers
```

---

### 4. Update CLAUDE.md

Add reference to standards:
```markdown
## Standards
See `agent-os/standards/` for coding conventions:
- `index.yml` - Standards index
- `global/` - Cross-language standards
- `backend/` - Django patterns
- `testing/` - Test patterns
```

---

## Output

```
## Standards Initialized

### Files Created/Updated
- [x] agent-os/standards/index.yml
- [x] agent-os/standards/global/coding-style.md
- [x] agent-os/standards/global/conventions.md
- [x] agent-os/standards/backend/python-django.md
- [x] agent-os/standards/backend/api.md
- [x] agent-os/standards/testing/test-writing.md

### Conventions Set
| Language | Formatter | Linter |
|----------|-----------|--------|
| Python | black | ruff/flake8 |

### Next Steps
- /execute <slug> - Standards will be applied
- /verify <slug> - Will check against standards
- /query "standards" - Search standards
```
