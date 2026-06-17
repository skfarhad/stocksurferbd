---
description: Final verification and commit. Mark feature as Done. Local only.
---

# /submit

Input: $ARGUMENTS

## Format
```
<slug>
```

---

## Rules
- All tests must pass
- Spec must be complete (all success criteria met)
- Local commit only (no push)

### Finding Existing Specs
To find an existing spec folder by slug:
```bash
ls agent-os/specs/ | grep <slug>
```

---

## Steps

### 1. Run full verification
Run `/verify <slug>` or manually:

```bash
docker compose exec be python manage.py test
docker compose exec be pytest tests/e2e/ -v
```

### 2. Check spec completeness
- Read `agent-os/specs/<YYYY-MM-DD>-<slug>/spec.md`
- All Success Criteria items marked complete
- Test plan executed
- All acceptance criteria met

### 3. Check tasks.md completeness
- Read `agent-os/specs/<YYYY-MM-DD>-<slug>/tasks.md`
- All tasks marked `[x]`
- All acceptance criteria in each task group met

### 4. Final commit
```bash
git add .
git commit -m "$(cat <<'EOF'
feat(<slug>): complete implementation

Changes:
- <summary of changes>

All tests passing
E2E verified in Docker
EOF
)"
```

### 5. Update spec docs
- Update `agent-os/specs/<YYYY-MM-DD>-<slug>/spec.md`:
  - Add completion note at top if desired
  - Ensure all Success Criteria checked
- Update `agent-os/specs/<YYYY-MM-DD>-<slug>/tasks.md`:
  - All tasks marked complete
  - Add final summary if desired

### 6. Cleanup (optional)
```bash
docker compose down
```

---

## Output

```
## Submission Complete

### Feature: <slug>
- Status: Done
- Branch: feature/<slug>
- Commit: <hash>
- Spec: agent-os/specs/<YYYY-MM-DD>-<slug>/

### Tests
| Check | Status |
|-------|--------|
| Unit tests | ✓ X/Y |
| E2E tests | ✓ X/Y |

### Summary
<brief summary of changes>

### Next Steps
- /merge-to <target> - Merge to target branch
```
