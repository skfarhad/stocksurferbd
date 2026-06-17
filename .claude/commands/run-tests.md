---
description: Run tests for this project. Supports Django. Mandatory after /execute.
---

# /run-tests

Input: $ARGUMENTS

## Format
```
<slug>
```

---

## Rules
- Read `agent-os/specs/<YYYY-MM-DD>-<slug>/spec.md` Test plan (if slug provided)
- Update tasks.md with test results
- All tests run inside Docker
- **MANDATORY** - Must run after `/execute` completes

### Finding Existing Specs
To find an existing spec folder by slug:
```bash
ls agent-os/specs/ | grep <slug>
```

---

## Steps

### 1. Read Spec Test Plan (if slug provided)

Check `agent-os/specs/<YYYY-MM-DD>-<slug>/spec.md` for:
- Required test types
- Specific test scenarios
- Coverage requirements

---

### 2. Run Django Backend Tests

```bash
# All Django tests
docker compose exec be python manage.py test

# Specific app
docker compose exec be python manage.py test apps.<app>

# Specific test class
docker compose exec be python manage.py test apps.<app>.tests.Test<Class>

# Specific test method
docker compose exec be python manage.py test apps.<app>.tests.Test<Class>.test_<method>

# With coverage
docker compose exec be pytest --cov=apps --cov-report=term-missing
```

**Test locations:**
- Unit tests: `apps/<app>/tests/test_<module>.py`
- Integration tests: `apps/<app>/tests/test_<feature>_integration.py`
- E2E tests: `tests/e2e/`

---

### 3. Create Test Fixtures (if needed)

```python
# apps/<app>/fixtures/<slug>_data.json
[
  {
    "model": "app.Model",
    "pk": 1,
    "fields": { ... }
  }
]
```

---

### 4. Implement Missing Tests

#### Django Unit Test Template
```python
from django.test import TestCase

class <Feature>Tests(TestCase):
    fixtures = ['<slug>_data.json']
    
    def test_<scenario>(self):
        pass
```

---

### 5. Run Full Test Suite

```bash
# Django
docker compose exec be python manage.py test

# E2E
docker compose exec be pytest tests/e2e/ -v
```

---

### 6. Update Spec and Tasks

Update `agent-os/specs/<YYYY-MM-DD>-<slug>/tasks.md`:
- Mark testing tasks complete
- Record test counts and results

Update `agent-os/specs/<YYYY-MM-DD>-<slug>/spec.md`:
- Add test file paths to Testing Strategy section
- Record coverage metrics if available

---

## Output

```
## Test Results

### Django Backend
- Tests run: X
- Passed: X
- Failed: X
- Coverage: X%

### Summary
- Total: X tests
- Status: ✓ All passing / ✗ X failures

### Next Steps
- /verify <slug> - Run full verification
- /merge-to <target> - Merge to target branch (only if tests pass)
```
