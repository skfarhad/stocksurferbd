---
description: Initialize or update project roadmap. Creates/updates agent-os/product/roadmap.md.
---

# /init-project-roadmap

## Rules
- Run once per project (or when major replanning needed)
- Creates/updates roadmap in `agent-os/product/roadmap.md`
- Interview user for project goals and priorities
- Links to spec folders in `agent-os/specs/`

---

## Steps

### 1. Check Existing Product Docs

Check if `agent-os/product/` already exists:
```
agent-os/product/
├── mission.md      # Product mission and vision
├── roadmap.md      # Feature roadmap
└── tech-stack.md   # Technology decisions
```

If exists, ask: "Roadmap exists. Update or full refresh?"

---

### 2. Interview for Project Vision

Ask using conversation (not all at once):

**Core Questions:**
- What is the product's main goal for the next milestone?
- Who are the target users (power users, casual, enterprise)?
- What are the must-have features (MVP for next release)?
- What are nice-to-have features?

**Technical Questions:**
- Any new integrations needed?
- API versioning considerations?
- New Celery background tasks?

**Constraints:**
- Any hard deadlines or constraints?
- Dependencies on external systems (APIs, providers)?
- Team capacity considerations?

---

### 3. Create/Update `agent-os/product/roadmap.md`

Use this template structure:

```markdown
# Product Roadmap

## MVP Phase (Current Focus)

1. [ ] <Feature Name> — <Description>. `S|M|L|XL`

2. [ ] <Feature Name> — <Description>. `S|M|L|XL`

## Phase 2: Enhancement and Scaling

3. [ ] <Feature Name> — <Description>. `S|M|L|XL`

## Phase 3: Enterprise and Infrastructure

4. [ ] <Feature Name> — <Description>. `S|M|L|XL`

## Phase 4: Future Vision

5. [ ] <Feature Name> — <Description>. `S|M|L|XL`

## Prioritization Framework

### High Priority (Core MVP)
Items 1-X are critical path to delivering the foundational value proposition.

### Medium Priority (Differentiation)
Items X-Y significantly enhance user experience and create competitive moats.

### Strategic Priority (Enterprise)
Items Y-Z are required for enterprise market penetration.

### Future Innovation
Items Z+ represent long-term vision and R&D investments.

## Success Criteria Per Phase

### MVP Success
- <metric 1>
- <metric 2>

### Phase 2 Success
- <metric 1>
- <metric 2>

## Notes
- Roadmap ordered by technical dependencies and strategic value delivery
- Each item represents an end-to-end functional and testable feature
- Security and privacy considerations embedded in every feature
```

---

### 4. Cross-Reference with Existing Specs

Check for existing specs:
- `agent-os/specs/*/spec.md`
- Active branches (`feature/*`, `bugfix/*`, `refactor/*`)

Link existing specs to roadmap items and identify gaps needing new specs.

---

### 5. Service-Specific Considerations

- New Django apps needed?
- New Celery tasks?
- New adapters or integrations?
- API versioning considerations?

---

### 6. Create Supporting Product Docs (if missing)

#### `agent-os/product/mission.md`
```markdown
# Product Mission

## Vision
<What does this product aspire to become?>

## Mission
<What problem does this product solve today?>

## Values
- <Value 1>
- <Value 2>
- <Value 3>

## Target Users
- <User persona 1>
- <User persona 2>
```

#### `agent-os/product/tech-stack.md`
```markdown
# Technology Stack

## Backend Services
| Service | Technology | Purpose |
|---------|------------|---------|
| Django Backend | Django 4.2, DRF | Core API |
| Celery | RabbitMQ | Background tasks |

## Databases
| Database | Purpose |
|----------|---------|
| PostgreSQL | Primary data store |
| Redis | Caching, sessions |

## Infrastructure
| Service | Provider |
|---------|----------|
| Hosting | Railway |
| Container | Docker |
```

---

## Output

```
## Roadmap Initialized

### Phases Created
- Phase 1 (MVP): X features
- Phase 2 (Enhancement): X features
- Phase 3 (Enterprise): X features
- Phase 4 (Future): X features

### Existing Specs Linked
- <spec-folder> → Roadmap Item #X
- <spec-folder> → Roadmap Item #Y

### Next Steps
- /plan <slug> - Plan individual features
- /feature-new <slug> - Create new feature spec
- /query "roadmap" - Review roadmap details
```
