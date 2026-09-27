# God Object Analysis Workflow

Identify and analyze god objects in the codebase using churn × complexity metrics. Find models that have grown too large and complex, then provide actionable recommendations for decomposition.

## Contents

- [God Object Indicators](#god-object-indicators)
- [Analysis Process](#analysis-process)
- [Output Format](#output-format)
- [Decomposition Strategies](#decomposition-strategies)
- [Related](#related)

## God Object Indicators

### Quantitative Signals

| Metric | Warning | Critical |
|--------|---------|----------|
| Lines of code | >250 | >500 |
| Methods | >20 | >40 |
| Associations | >10 | >20 |
| Callbacks | >5 | >10 |
| Concerns included | >5 | >10 |
| Scopes | >10 | >20 |

### Churn Analysis

High change frequency indicates:
- Central to business logic (expected)
- Accumulating unrelated features (problem)
- Frequent bug fixes (complexity debt)

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

### Complexity Indicators

- Many conditionals (case/if statements)
- Mixed responsibilities (authentication + billing + notifications)
- State-dependent behavior (many boolean checks)
- External API integration mixed with domain logic

## Analysis Process

### 1. Identify Candidates

```python
from pathlib import Path
models = sorted((p for p in Path(".").glob("*/models.py")), key=lambda p: len(p.read_text().splitlines()), reverse=True)
for filename in models:
    print(filename, len(filename.read_text().splitlines()))
# Also inspect split models/ packages; line count is a lead, never a verdict.
```

### 2. Analyze Each Candidate

For each god object candidate:

1. **Count structural elements**
   - Lines, methods, associations, callbacks, scopes, concerns

2. **Identify responsibility clusters**
   - Group related methods by what they do
   - Look for natural extraction boundaries

3. **Check for layer violations**
   - Presentation logic (formatting, view helpers)
   - Infrastructure concerns (direct API/SDK calls)
   - Application logic (orchestration, notifications/mailers, authorization)

4. **Map dependencies**
   - What other models does it touch?
   - What services/jobs reference it?

### 3. Recommend Decomposition

For each cluster of responsibilities, suggest:
- Concern extraction (shared behavior)
- Service extraction (operations)
- Value object extraction (data + behavior)
- Associated object extraction (delegated responsibilities)

## Output Format

```markdown
# God Object Analysis

## Summary
- Models analyzed: 45
- God object candidates: 4
- Critical (>500 lines): 1
- Warning (>250 lines): 3

## Critical: User (623 lines)

### Metrics
| Metric | Value | Status |
|--------|-------|--------|
| Lines | 623 | 🔴 Critical |
| Methods | 47 | 🔴 Critical |
| Associations | 15 | 🟡 Warning |
| Callbacks | 8 | 🟡 Warning |
| Concerns | 6 | 🟡 Warning |
| Scopes | 12 | 🟡 Warning |
| Churn (6mo) | 89 commits | High |

### Responsibility Clusters

**Authentication (lines 45-120)**
- `authenticate`, `valid_password?`, `reset_password!`
- `generate_token`, `verify_token`, `invalidate_sessions`
→ Extract to `accounts.authentication` concern or service

**Profile Management (lines 125-200)**
- `update_profile`, `avatar_url`, `display_name`
- `bio`, `social_links`, `preferences`
→ Extract to `UserProfile` associated object

**Billing (lines 205-320)**
- `subscribe!`, `cancel_subscription!`, `update_payment_method`
- `invoice_history`, `current_plan`, `billing_email`
→ Extract to `UserBilling` associated object or service

**Notifications (lines 325-400)**
- `notify!`, `notification_preferences`, `unread_count`
- `email_notifications?`, `push_notifications?`
→ Extract to `UserNotificationSettings` value object

**Authorization (lines 405-480)**
- `can_access?`, `permissions`, `role_for`
- `admin?`, `moderator?`, `member_of?`
→ Extract to `UserPolicy` (already should be there)

### Recommended Extraction Plan

1. **Immediate**: Extract billing to `UserBilling` using `explicit composition`
2. **Short-term**: Move notification settings to value object
3. **Medium-term**: Review authentication for service extraction
4. **Ongoing**: Move authorization checks to policies

### Code Example

Before:
```python
# Audit model methods by responsibility and call sites, not size alone.
model_tree = ast.parse(Path("accounts/models.py").read_text())
```

After:
```python
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100)
# Core authentication remains in the configured Django user model.
```

## Warning: Order (380 lines)

### Metrics
| Metric | Value | Status |
|--------|-------|--------|
| Lines | 380 | 🟡 Warning |
| Methods | 28 | 🟡 Warning |
| State methods | 12 | High |
| Callbacks | 6 | 🟡 Warning |

### Responsibility Clusters

**State Management (lines 50-150)**
- Multiple status checks, transitions, validations
→ Extract to state machine (explicit transitions)

**Pricing Calculation (lines 155-220)**
- `calculate_subtotal`, `apply_discount`, `tax_amount`, `total`
→ Extract to `OrderTotals` value object

**Fulfillment (lines 225-300)**
- `ship!`, `deliver!`, `tracking_info`, `estimated_delivery`
→ Extract to `fulfill_order` service or associated object

### Recommended Extraction Plan

1. **Immediate**: Implement state machine for order status
2. **Short-term**: Extract pricing to calculator object
3. **Medium-term**: Consider fulfillment service

## Non-Issues

### Post (280 lines)
- Lines are high but complexity is low
- Single responsibility (content management)
- High churn due to feature additions, not bug fixes
- **Assessment**: Monitor but no action needed

## Extraction Priority Matrix

| Model | Lines | Churn | Complexity | Priority |
|-------|-------|-------|------------|----------|
| User | 623 | High | High | 🔴 Critical |
| Order | 380 | Medium | High | 🟡 High |
| Post | 280 | High | Low | 🟢 Monitor |
| Comment | 260 | Low | Low | 🟢 Low |
```

## Decomposition Strategies

### 1. Concern Extraction
For shared behavior across models:
```python
class Sluggable(models.Model):
    slug = models.SlugField(unique=True)
    class Meta:
        abstract = True
```

### 2. Associated Object (explicit composition)
For delegated responsibilities:
```python
billing = Billing(customer_id=user.billing_customer_id, client=billing_client)
invoices = billing.invoice_history()
```

### 3. Value Object (composed_of)
For data with behavior:
```python
address = Address(country=user.country, city=user.city, street=user.street, postal_code=user.postal_code)
```

### 4. Service Extraction
For operations that span boundaries:
```python
user = register_user(username=username, password=password)
```

### 5. State Machine
For complex state management:
```python
def confirm(order):
    if order.status != "pending":
        raise InvalidTransition("Only pending orders can be confirmed")
    order.status = "confirmed"
```

## Related

- [Extraction signals](../references/core/extraction-signals.md)
- [Service Objects pattern](../references/patterns/service-objects.md)
- [Concerns pattern](../references/patterns/concerns.md)
- [Value Objects pattern](../references/patterns/value-objects.md)
- [God object decomposition example](../examples/god-object-decomposition.md)
