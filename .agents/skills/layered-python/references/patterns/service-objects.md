# Service Objects

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Conventions to Establish
- Anti-Patterns
- From Services to Abstractions
- Related Mechanisms

## Summary

Service objects represent single business operations between controllers and models. They fill the gap in Django's request/model boundary where neither controllers (inbound layer) nor models (domain layer) are appropriate homes for business logic orchestration.

## When to Use

- Orchestrating multiple domain objects for a use case
- Operations that span multiple models with transaction boundaries
- Complex business logic that doesn't belong in any single model
- Reusable operations called from multiple controllers

## When NOT to Use

- Simple CRUD operations (let controller handle)
- Domain logic (belongs in models)
- Single-model operations (keep in model)

## Key Principles

- **Waiting room metaphor** — services are temporary homes until proper abstractions emerge
- **Establish conventions early** — naming, explicit inputs, return values and errors; a base class is optional
- **Services orchestrate, models know rules** — don't strip domain logic into services
- **Avoid bag of random objects** — decompose into specialized abstractions as patterns emerge

## Implementation

### Base Class

```python
# No base service is required. Use a function with keyword-only domain inputs.
def publish_post(*, post, actor):
    post.publish(by=actor)
    post.save()
```

### Example Service

```python
def handle_github_event(*, event):
    user = User.objects.get(gh_id=event.user_id)
    match event:
        case IssueOpened(title=title, body=body):
            return user.issues.create(title=title, body=body)
        case PullRequestOpened(title=title, body=body, branch=branch):
            return user.pull_requests.create(title=title, body=body, branch=branch)
        case _:
            raise UnsupportedEvent(type(event).__name__)
```

### Usage

```python
def github_callback(request):
    event = parse_verified_github_event(request)
    handle_github_event(event=event)
    return HttpResponse(status=204)
```

## Conventions to Establish

| Decision | Options |
|----------|---------|
| Naming | `handle_github_event` or `HandleGithubEvent` |
| Interface | Named function, or __call__ when a stateful callable is useful |
| Shared machinery | Extract a focused function only after actual repetition |
| Return values | Result objects, monads, or plain values |
| Error handling | Exceptions, result objects, or monads |

## Anti-Patterns

### Anemic Models

All logic moved to services, models become pure data containers:

```python
# Bad: an application service owns a calculation belonging to the order.
def calculate_order_total(order, items):
    return sum((item.price * item.quantity for item in items), Decimal("0"))
```

**Fix:** Keep domain logic in models:

```python
class Order(models.Model):
    def total(self, *, items):
        return sum((item.subtotal() for item in items), Decimal("0"))
```

### Bag of Random Objects

No conventions, each service is unique:

```python
user = registration.perform(attributes)  # User or None
order = OrderProcessor.process(order_id)  # Incompatible exception contract
```

### Premature Abstraction

Creating service infrastructure before patterns emerge:

```python
class BaseCommand(CommandPattern, ResultMonad, TransactionWrapper):
    pass  # Anti-example: infrastructure invented before a concrete operation.
```

**Fix:** Start simple, extract patterns after you see repetition.

## From Services to Abstractions

As services accumulate, decompose into specialized patterns:

- **Form objects** — user input handling
- **Query objects** — complex queries
- **Policy objects** — authorization
- **Presenter objects** — view logic

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| Python signatures | Explicit required keyword-only inputs |
| Dataclasses and exceptions | Typed values and narrow failure contracts |
