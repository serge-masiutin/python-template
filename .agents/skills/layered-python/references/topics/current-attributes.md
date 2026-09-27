# Current Attributes

## Contents

- Summary
- Layer Placement
- Key Principles
- Implementation
- Acceptable Uses of Current
- Anti-Patterns
- Where Current IS Appropriate
- Testing with Current
- Current vs Explicit Parameters

## Summary

Django passes request context on HttpRequest; Python ContextVar can scope observability metadata. It is not an authorization or tenant mechanism. Pass actor and tenant explicitly to operations and queries.

## Layer Placement

```
┌─────────────────────────────────────────┐
│ Presentation Layer                      │
│  └─ Sets Current values in controllers  │
├─────────────────────────────────────────┤
│ Application Layer                       │
│  └─ May read Current (sparingly)        │
├─────────────────────────────────────────┤
│ Domain Layer                            │
│  └─ Should NOT access Current           │
└─────────────────────────────────────────┘
```

## Key Principles

- **Set at entry points** — controllers, jobs, middleware
- **Read sparingly** — prefer explicit parameters
- **Never in models** — domain layer must be Current-agnostic
- **Reset explicitly** — always reset ContextVar tokens in finally; Django does not reset custom ContextVars

## Implementation

### Basic Current Class

```python
from contextvars import ContextVar
request_id = ContextVar("request_id")  # Observability only, never business authority.
```

### Setting in Controllers

```python
def request_context(get_response):
    def middleware(request):
        token = request_id.set(str(uuid.uuid4()))
        try:
            return get_response(request)
        finally:
            request_id.reset(token)
    return middleware
```

### Multi-Tenancy with Current

```python
tenant = get_object_or_404(Tenant, subdomain=subdomain)
# Membership is verified before the tenant is passed to operations.
operation(actor=request.user, tenant=tenant)
```

### In Background Jobs

```python
def process_order_job(*, order_id, actor_id, tenant_id):
    actor = User.objects.get(pk=actor_id, is_active=True)
    tenant = Tenant.objects.get(pk=tenant_id)
    return process_order(order_id=order_id, actor=actor, tenant=tenant)
# The operation checks current execution authority; queued IDs do not grant access.
```

## Acceptable Uses of Current

### Audit Logging

```python
@transaction.atomic
def update_post(*, post, actor, title):
    post.title = title
    post.updated_by = actor
    post.save(update_fields=["title", "updated_by"])
```

### Request Logging

```python
logger.info("request_completed", extra={"request_id": request_id.get(), "status_code": response.status_code})
# Exclude emails, names, cookies, bodies and other private request data.
```

### Time Zone

```python
from django.utils import timezone
from zoneinfo import ZoneInfo
with timezone.override(ZoneInfo(user.time_zone)):
    displayed = timezone.localtime(record.created_at)
# Scope overrides and restore them at the boundary.
```

## Anti-Patterns

### Ambient context in Models (Domain Layer)

```python
form = PostForm(request.POST)
if form.is_valid():
    post = form.save(commit=False)
    post.author = request.user
    post.save()
```

### Current for Business Logic

```python
def can_publish(*, actor, post):
    return actor.is_superuser or post.author_id == actor.pk
```

### Current in Service Objects

```python
def publish_post(*, post, actor):
    if not can_publish(actor=actor, post=post):
        raise PermissionDenied
    post.publish(at=timezone.now())
    post.save(update_fields=["published_at"])
```

### Testing Difficulties

```python
@pytest.mark.django_db
def test_post_author_is_explicit(user):
    post = Post.objects.create(author=user, title="Test")
    assert post.author_id == user.pk
```

## Where Current IS Appropriate

| Use Case | Appropriate? | Notes |
|----------|--------------|-------|
| Audit trails | ⚠️ | Pass actor explicitly; ambient request ID may annotate logs |
| Request logging | ✅ | Infrastructure concern |
| Time zone | ✅ | Presentation concern |
| Locale | ✅ | Presentation concern |
| Multi-tenancy | ❌ | Pass an authorized tenant explicitly and scope every query |
| Authorization | ❌ | Use policies |
| Business logic | ❌ | Pass explicitly |
| Model behavior | ❌ | Domain should be agnostic |

## Testing with Current

```python
def test_observability_context_resets():
    token = request_id.set("test-request")
    try:
        assert request_id.get() == "test-request"
    finally:
        request_id.reset(token)
    with pytest.raises(LookupError):
        request_id.get()
```

## Current vs Explicit Parameters

| Approach | Pros | Cons |
|----------|------|------|
| Current | Less logging boilerplate, context-local propagation | Hidden dependencies, testing complexity |
| Explicit | Clear dependencies, easy testing | More verbose, must pass through layers |

**Recommendation**: Default to explicit parameters. Use Current only for cross-cutting infrastructure concerns (logging, audit, time zone).
