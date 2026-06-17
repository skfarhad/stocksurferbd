# /investigate - End-to-End Root Cause Analysis

Perform comprehensive investigation across the project to identify root causes.

## Usage

```
/investigate <environment> <bearer_token> [problem_description]
```

## Parameters

- **environment** (required): `local`, `predev`, or `dev`
- **bearer_token** (required): JWT token for API authentication
- **problem_description** (optional): Brief description of the issue

## Examples

```
/investigate dev eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
/investigate predev eyJ... "emails not syncing from Gmail"
/investigate local eyJ... "Slack messages not appearing"
```

## What This Command Does

1. **Environment Setup**: Configures API endpoints and Railway CLI
2. **Health Check**: Verifies API and account health status
3. **Sync Analysis**: Reviews sync logs for errors and patterns
4. **Celery Investigation**: Checks task queues and scheduled jobs
5. **Database Queries**: Examines account and sync data directly
6. **Service-Specific Checks**: Gmail, Outlook, Slack, WhatsApp
7. **iOS Client Review**: Checks mobile app configuration
8. **Recovery Actions**: Provides manual sync and re-auth options
9. **Report Generation**: Produces structured root cause analysis

## Investigation Flow

```
┌─────────────────┐
│ Health Check    │ → API responding? Accounts healthy?
└────────┬────────┘
         │
┌────────▼────────┐
│ Account Status  │ → Token expired? Webhook issues?
└────────┬────────┘
         │
┌────────▼────────┐
│ Sync Logs       │ → Recent failures? Error patterns?
└────────┬────────┘
         │
┌────────▼────────┐
│ Celery Tasks    │ → Workers running? Beat scheduling?
└────────┬────────┘
         │
┌────────▼────────┐
│ Database        │ → Stuck syncs? Data consistency?
└────────┬────────┘
         │
┌────────▼────────┐
│ Service Check   │ → Gmail/Outlook/Slack/WhatsApp
└────────┬────────┘
         │
┌────────▼────────┐
│ Root Cause      │ → Identify cause with accuracy %
│ Report          │ → Recommend fixes
└─────────────────┘
```

## Output Format

The investigation produces a structured report:

```markdown
# Root Cause Analysis Report

## Environment: dev
## Investigation Date: 2026-01-24

## Account Status Summary
| Account | Provider | Status | Issues |
|---------|----------|--------|--------|

## Root Causes (Sorted by Accuracy)
### #1: [Cause] (99% accuracy)
### #2: [Cause] (95% accuracy)

## Immediate Actions Required
1. [ ] Action 1
2. [ ] Action 2

## Available Recovery APIs
- Manual sync: POST /api/v0/conversation/accounts/{id}/sync/
- Re-auth: GET /api/v0/common/oauth/auth/?provider={provider}
```

## Common Issues Detected

| Issue | Detection Method | Auto-Fix Available |
|-------|------------------|-------------------|
| Token expired | Health API `token_expired` | Re-auth URL provided |
| Webhook expired | Health API `webhook_expired` | Manual sync triggers renewal |
| Sync stale | Health API `sync_stale` | Manual sync |
| Stuck syncs | Sync logs `status=running` > 1hr | DB cleanup query |
| Scheduler stopped | No recent sync logs | Celery restart needed |
| Date parsing bug | Error `year XXXXX out of range` | Code fix required |

## Skill Reference

See `.claude/skills/investigate/skill.md` for detailed investigation procedures.
