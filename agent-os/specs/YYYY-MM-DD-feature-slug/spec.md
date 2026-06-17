# Feature Specification: [Feature Name]

## Overview

### Objective
<!-- One sentence describing what this feature accomplishes -->
[TODO: Describe the objective]

### Background
<!-- Why is this needed? Link to raw-idea.md if applicable -->
[TODO: Provide background context]

### Scope
- **In Scope**: [List what's included]
- **Out of Scope**: [List what's explicitly excluded]

---

## User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-1 | [User type] | [Action] | [Benefit] |
| US-2 | [User type] | [Action] | [Benefit] |

---

## Technical Design

### Architecture Overview
<!-- High-level architecture description -->
```
[Diagram or description of component interactions]
```

### Data Model Changes

#### New Models
```python
# apps/<app>/models.py

class NewModel(models.Model):
    """Description of the model."""
    field_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'app_newmodel'
```

#### Model Modifications
- `ExistingModel`: Add `new_field` (CharField, max_length=50, nullable)

### API Endpoints

#### `POST /api/v0/<resource>/`
- **Description**: [What this endpoint does]
- **Auth**: JWT required
- **Request Body**:
```json
{
  "field1": "string",
  "field2": 123
}
```
- **Response** (201):
```json
{
  "id": 1,
  "field1": "string",
  "field2": 123,
  "created_at": "2024-01-01T00:00:00Z"
}
```
- **Errors**: 400 (validation), 401 (unauthorized), 500 (server error)

#### `GET /api/v0/<resource>/{id}/`
- **Description**: [What this endpoint does]
- **Auth**: JWT required
- **Response** (200):
```json
{
  "id": 1,
  "field1": "string",
  "field2": 123
}
```

### Frontend Changes

#### New Components
- `ComponentName.js` - [Description]

#### Modified Components
- `ExistingComponent.js` - [What changes]

---

## Acceptance Criteria

### Functional
- [ ] AC-1: [Specific testable criterion]
- [ ] AC-2: [Specific testable criterion]
- [ ] AC-3: [Specific testable criterion]

### Non-Functional
- [ ] AC-4: API response time < 500ms
- [ ] AC-5: Test coverage > 80%

---

## Test Plan

### Unit Tests
| Test | Description | Location |
|------|-------------|----------|
| `test_<name>` | [What it tests] | `apps/<app>/tests/test_<file>.py` |

### Integration Tests
| Test | Description |
|------|-------------|
| [Test name] | [What it tests] |

### Manual Testing Checklist
- [ ] [Test scenario 1]
- [ ] [Test scenario 2]

---

## Migration Plan

### Database Migrations
1. `python manage.py makemigrations <app>`
2. `python manage.py migrate`

### Data Migration (if needed)
- [Description of data migration steps]

### Rollback Plan
- [How to rollback if issues occur]

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [Mitigation strategy] |

---

## References
- [Link to related docs]
- [Link to design mockups]
- [Link to external resources]
