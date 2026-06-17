---
description: Implement per spec for Django/DRF project. Small commits. Run tests in Docker. Local only. Works with features, bugfixes, and refactors.
---

# /execute

Input: $ARGUMENTS

## Format A (Preferred): YAML block
```
slug: user-export
type: feature  # feature | bugfix | refactor (auto-detected from branch if omitted)
service: django  # django | all (auto-detected if omitted)
notes: |
  Session context or focus areas.
```

## Format B: One-liner
```
user-export --type feature --service django --notes "focus on backend only"
```

---

## Rules
- Must be on correct branch (`feature/<slug>`, `bugfix/<slug>`, or `refactor/<slug>`)
- Follow spec at `agent-os/specs/<YYYY-MM-DD>-<slug>/spec.md`
- Update `agent-os/specs/<YYYY-MM-DD>-<slug>/tasks.md` after each task
- Scope changes require spec update first
- Run tests after each significant change
- Local commits only (no push)

## Type Detection
If `type` not provided, detect from current branch:
- `feature/<slug>` → feature
- `bugfix/<slug>` → bugfix
- `refactor/<slug>` → refactor

## Service Detection
If `service` not provided:
1. Check spec for affected services
2. Check files modified in spec
3. Default to `all` if unclear

## Path Mapping
| Type | Branch | Spec Folder | Commit Prefix |
|------|--------|-------------|---------------|
| feature | `feature/<slug>` | `agent-os/specs/<YYYY-MM-DD>-<slug>/` | `feat(<slug>):` |
| bugfix | `bugfix/<slug>` | `agent-os/specs/<YYYY-MM-DD>-<slug>/` | `fix(<slug>):` |
| refactor | `refactor/<slug>` | `agent-os/specs/<YYYY-MM-DD>-<slug>/` | `refactor(<slug>):` |

### Finding Existing Specs
To find an existing spec folder by slug:
```bash
ls agent-os/specs/ | grep <slug>
```

---

## Steps

### Step 1: Parse $ARGUMENTS
Extract:
- slug (required, lowercase, hyphen-separated)
- type (optional, auto-detected)
- service (optional, auto-detected)
- notes (optional - session context or focus areas)

### Step 2: Verify branch and read spec
1. Confirm branch matches `<type>/<slug>`
2. Find spec folder: `ls agent-os/specs/ | grep <slug>`
3. Read spec and tasks.md, restate:
   - Objective
   - Acceptance criteria / Fix criteria / Refactor goals
   - Affected services
   - Test plan

### Step 3: Implement based on service

#### For Django Backend (`apps/`, `config/`):
- Create/update models
- Generate and apply migrations: `docker compose exec be python manage.py makemigrations && docker compose exec be python manage.py migrate`
- Create views and URLs
- Create templates and static files
- Add Celery tasks if needed

### Step 4: After each increment

#### Django:
```bash
docker compose exec be python manage.py test apps.<app>
docker compose logs be --tail=50
```

#### Commit changes:
```bash
git add <files>
git commit -m "<prefix> <description>"
```
Use commit prefix from Path Mapping table.

### Step 5: Update tracking
1. Mark completed tasks in `agent-os/specs/<YYYY-MM-DD>-<slug>/tasks.md`
2. Add session notes if needed
3. Mark completed checklist items in spec

---

## Output
- Summary of changes per service
- Tests run + results
- Commits made
- tasks.md updates

## Next Commands
- `/run-tests <slug>` - **MANDATORY** Run full test suite
- `/resume-execute <slug>` - Continue after break
- `/progress-status <slug>` - Check progress
- `/verify <slug>` - Run full verification
- `/merge-to <target>` - Merge to target branch
- `/submit <slug>` - Final submission

## IMPORTANT
**After execution completes, `/run-tests` is MANDATORY.** Always ask the user:
> "Execution complete. Ready to run `/run-tests <slug>`?"

Wait for explicit user confirmation before proceeding.

**DO NOT run `/merge-to` until `/run-tests` passes.**
