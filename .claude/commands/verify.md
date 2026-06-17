---
description: Run all quality checks and tests. Verify feature is complete.
---

# /verify

Input: $ARGUMENTS

## Format
```
<slug>
```

---

## Rules
- All checks run inside Docker
- Must pass before marking feature complete
- Update spec with results

### Finding Existing Specs
To find an existing spec folder by slug:
```bash
ls agent-os/specs/ | grep <slug>
```

---

## Steps

### 1. Start Docker Environment
```bash
docker compose up -d
docker compose ps  # Verify all services running
```

---

### 2. Django Backend Verification

#### Migrations
```bash
docker compose exec be python manage.py migrate
docker compose exec be python manage.py check
docker compose exec be python manage.py showmigrations --list
```

#### Linting
```bash
docker compose exec be ruff check .
docker compose exec be black --check .
```

#### Type Checking (if configured)
```bash
docker compose exec be mypy apps/
```

#### Unit Tests
```bash
docker compose exec be python manage.py test
```

#### Coverage
```bash
docker compose exec be pytest --cov=apps --cov-report=term-missing
```

---

### 3. E2E Tests

```bash
# Django E2E
docker compose exec be pytest tests/e2e/ -v
```

---

### 4. Manual Verification

- Check Docker logs: `docker compose logs be --tail=100`
- Access API docs: http://localhost:8001/swagger/
- Test key endpoints manually

---

### 5. Update Spec Docs

Update `agent-os/specs/<YYYY-MM-DD>-<slug>/spec.md`:
- Record verification results
- Mark Success Criteria items as verified

Update `agent-os/specs/<YYYY-MM-DD>-<slug>/tasks.md`:
- Note verification status
- Record any issues found

---

## Output

```
## Verification Results

### Django Backend
| Check | Status |
|-------|--------|
| Migrations | ✓ / ✗ |
| Django check | ✓ / ✗ |
| Linting | ✓ / ✗ |
| Type check | ✓ / ✗ |
| Unit tests | ✓ X/Y passed |
| Coverage | X% |

### E2E Tests
| Test | Status |
|------|--------|
| <test_name> | ✓ / ✗ |

### Summary
- All checks: ✓ Passing / ✗ X failures
- Feature status: Verified / Needs fixes

### Issues Found
- (none or list with severity)

### Next Steps
- /merge-to <target> - Merge to target branch (if verified)
- /submit <slug> - Final submission
```
