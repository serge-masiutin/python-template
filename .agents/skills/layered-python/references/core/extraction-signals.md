# Extraction Signals

How to identify code that should be extracted to a different layer or abstraction.

## Contents

- Callback Scoring System
- God Object Identification
- Concern Health Check
- Service Object Signals
- Controller Fat Signals
- Quick Reference
- Static Analysis Tools

## Callback Scoring System

Rate model callbacks to identify extraction candidates:

| Score | Type | Description | Action |
|-------|------|-------------|--------|
| 5/5 | **Transformer** | Computes/defaults required values | Keep in model |
| 4/5 | **Normalizer** | Sanitizes input data | Keep (prefer `.normalizes` API) |
| 4/5 | **Utility** | Counter caches, cache busting | Keep in model |
| 2/5 | **Observer** | Side effects after commit | Review case-by-case |
| 1/5 | **Operation** | Business process steps | Extract immediately |

### Transformer Callbacks (Keep)

Compute or default required attribute values:

```python
class Post(models.Model):
    def prepare_content(self):
        self.slug = slugify(self.title)
        self.word_count = len(self.content.split())
# Call explicitly from the write operation, before validation and persistence.
```

### Normalizer Callbacks (Keep)

Sanitize user input. Normalize at the Form.clean_<field>() boundary:

```python
class PostForm(forms.ModelForm):
    def clean_title(self):
        return self.cleaned_data["title"].strip()
```

### Utility Callbacks (Keep)

Framework-level utilities like counter caches:

```python
# Prefer a query count until measurement justifies a persisted counter.
posts = Post.objects.annotate(comment_count=Count("comments"))
# A persisted counter needs atomic increments and reconciliation for bulk writes.
```

### Operation Callbacks (Extract)

Signs of misplacement:
- Conditions (`unless: :admin?`)
- Collaboration with non-model objects (mailers, API clients)
- Remote peer communication

```python
@receiver(post_save, sender=User)
def signup(sender, instance, created, **kwargs):
    if created:
        create_initial_project(instance)
        send_welcome_email(instance.pk)
        sync_crm(instance.pk)
```

**Extraction options:**
1. Move to controller
2. Move to service object
3. Use event-driven approach

```python
@transaction.atomic
def register_user(*, username, password):
    user = User.objects.create_user(username=username, password=password)
    DeliveryIntent.objects.create(user=user, event="user_registered")
    return user
# A worker dispatches the committed event under an explicit delivery contract.
```

## God Object Identification

### Churn × Complexity Metric

**Churn** = how often a file changes (indicates ongoing modifications)
**Complexity** = code complexity score (use Flog)

Files high in both are prime refactoring candidates.

```bash
# Calculate churn
git log --format=oneline -- <feature>/models/user.py | wc -l

# Calculate complexity
# Inspect branch count and nesting; use a configured Python analyzer if installed.

# Find intersection of top 10 by each
```

### Automated Tool

Use [attractor](https://github.com/julianrubisch/attractor):

```bash
attractor report -p app/models
```

### Common God Object Names

Watch for these accumulating responsibilities:
- `User` / `Account`
- `Order` / `Transaction`
- `Project` / `Workspace`
- `Post` / `Article`

### Decomposition Strategies

1. **Extract concerns** for shared behaviors
2. **Extract delegate objects** for complex operations
3. **Extract value objects** for groups of related attributes
4. **Create new models** for distinct concepts

```python
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100)

class NotificationPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email_enabled = models.BooleanField(default=True)
```

## Concern Health Check

### Good Concerns (Behavioral)

Can be tested in isolation, shared across models:

```python
class Publishable(models.Model):
    published_at = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def publish(self, *, at):
        self.published_at = at
```

**Test:** Can you write specs for this concern without instantiating the host model?

### Bad Concerns (Code-Slicing)

Groups code by framework artifact type, not behavior:

```python
class ContactMixin:
    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        validate_email(self.email)
        return super().save(*args, **kwargs)
# A mixin with hidden validation and persistence hooks is still code-slicing.
```

**Test:** If removing this concern breaks unrelated tests, it's code-slicing.

### Overgrown Concerns

Signs a concern should be extracted:
- 50+ lines
- Multiple responsibilities
- Complex internal state

Extract to:
- **Delegate object** for operations
- **Value object** for attribute groups
- **Separate model** for distinct entity

## Service Object Signals

### When to Extract to Service

Extract from controller when you see:
- Multiple model operations in sequence
- Transaction spanning multiple models
- Complex error handling
- Reusable business operation

### When NOT to Use Services

Don't extract:
- Single model operations (keep in model)
- Simple CRUD (let controller handle)
- Domain logic (belongs in model, not service)

### Anemic Model Warning Signs

Your models might be anemic if:
- Services contain calculations that use only model data
- Models are pure data containers (associations + validations only)
- You have `CalculateXService` for model attributes
- Domain rules live in services, not models

```python
class Order(models.Model):
    def total(self, *, items):
        return sum((item.subtotal() for item in items), Decimal("0"))
# Domain arithmetic stays with the order; orchestration saves the result.
```

## Controller Fat Signals

### Extract When You See

- Business calculations (pricing, discounts)
- Multiple model updates
- Complex conditionals based on business rules
- External API calls
- More than 10-15 lines per action

### Keep in Controller

- Parameter parsing
- Authentication/authorization
- Response formatting
- Simple model operations

## Quick Reference

| Signal | Threshold | Action |
|--------|-----------|--------|
| Callback score | ≤ 2/5 | Extract to service/event |
| Model complexity | Flog > 100 | Decompose |
| Model churn | > 30 changes/year | Review for extraction |
| Concern size | > 50 lines | Extract to delegate |
| Controller action | > 15 lines | Extract to service |
| Service with domain logic | Any calculations | Move to model |

## Static Analysis Tools

| Tool | Purpose | Command |
|------|---------|---------|
| Python AST / existing analyzer | Branching and responsibility review | Inspect functions; use only installed tooling |
| [attractor](https://github.com/julianrubisch/attractor) | Churn × complexity | `attractor report` |
| [callback_hell](https://github.com/evilmartians/callback_hell) | Callback audit | `bin/rails callback_hell:callbacks[User]` |
