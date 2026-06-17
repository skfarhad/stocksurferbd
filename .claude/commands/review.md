# Code Review Command

Perform comprehensive code review following project standards.

## Review Focus

1. **Architecture**: Adapter pattern compliance, Service layer, Clean architecture
2. **Security**: Token encryption, webhook validation, OWASP Top 10
3. **Code Quality**: PEP 8, SOLID, DRY/KISS/YAGNI
4. **Django/DRF**: Models (UUIDs, indexes), Serializers, ViewSets, Celery
5. **Performance**: DB optimization, N+1 queries, caching
6. **Testing**: Coverage, mocking, AAA pattern

## Process

1. Read `CLAUDE.md` for project context
2. Examine changed files thoroughly
3. Check pattern adherence against codebase standards
4. Verify security requirements (tokens, webhooks, input validation)
5. Assess performance implications
6. Review test coverage
7. Provide specific file:line feedback with code examples

## Output Format

```markdown
## Code Review Summary

### ✅ Strengths
- [Positive aspects]

### ⚠️ Issues

#### 🔴 Critical (Must Fix)
- **file.py:123**: Issue → Fix

#### 🟡 Important (Should Fix)
- **file.py:456**: Issue → Solution

#### 🔵 Suggestions
- **file.py:789**: Current → Better

### 📊 Metrics
- Files: X | Security: X critical, X important
- Pattern compliance: X% | Tests: [status]

### ✅ Decision
- [ ] Ready to merge
- [ ] Approve with changes
- [ ] Request changes
```

## Key Patterns to Check

**Adapters**: ABC interface, required methods (authenticate, refresh_token, validate_webhook, handle_webhook, register_webhook), `@retry_with_backoff`, standardized responses

**Security**: Token encryption (`TokenEncryption`), webhook signatures, OAuth state validation, input validation (model + serializer), no hardcoded secrets

**Models**: UUID PKs, indexes, `clean()` + `save()`, timestamps, `help_text`

**Services**: `@transaction.atomic`, error handling, logging, ErrorRecoveryManager

**ViewSets**: Filter by user, `IsAuthenticated`, proper HTTP codes, `@action` for custom endpoints

**Celery**: `@shared_task(bind, max_retries, delay)`, retry logic, logging

## Critical Issues (Auto-fail)

**Hardcoded Field Names** (CRITICAL): All dictionary keys and response field names MUST use centralized constants from `apps/common/constants/fields.py`. Hardcoded strings like `'success'`, `'results'`, `'digest_text'`, `'qr_code'` are NOT acceptable.

```python
# 🔴 CRITICAL - Hardcoded strings
return {'success': True, 'message_count': count}
obj.configuration.get('qr_code')

# ✅ CORRECT - Use constants
from apps.common.constants.fields import ResponseFields, ConfigFields
return {ResponseFields.SUCCESS: True, ResponseFields.MESSAGE_COUNT: count}
obj.configuration.get(ConfigFields.QR_CODE)
```

Available constant classes: `ResponseFields`, `AccountFields`, `MessageFields`, `ConversationFields`, `ConfigFields`, `DailySummaryFields`, `ProcessingStateFields`, `StatusValues`, `KBPayloadFields`, `EventPayloadFields`

Be constructive and specific. Prioritize security and patterns over style.
