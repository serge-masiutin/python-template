# State Machines

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Identifying Implicit State Machines
- Implementation
- Events Over Direct Transitions
- Transition Guards
- Transition Callbacks
- Anti-Patterns
- Related Mechanisms

## Summary

State machines describe possible states, transitions between them, and triggering events. They make implicit state logic explicit and centralized, preventing scattered conditional logic across the codebase.

## When to Use

- Multiple related boolean/timestamp attributes tracking state
- Complex conditional logic based on object state
- State-dependent behavior
- Audit trail requirements

## When NOT to Use

- Linear progressions (just use enum)
- Simple two-state flags
- Before patterns emerge (premature)

## Key Principles

- **Identify implicit state machines** — scattered booleans/timestamps often hide state
- **Prefer events over direct transitions** — `order.submit!` not `order.status = :submitted`
- **Extract when not central** — standalone workflow for secondary state
- **Guards and callbacks sparingly** — don't recreate callback problems

## Identifying Implicit State Machines

Signs of hidden state:

```python
def can_publish(post):
    return post.submitted_at is not None and post.reviewed_at is not None and not post.is_hidden
# Several independent flags allow contradictory combinations.
```

## Implementation

### With Enum (Simple)

```python
class Post(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft"
        SUBMITTED = "submitted"
        APPROVED = "approved"
        REJECTED = "rejected"
        PUBLISHED = "published"
        ARCHIVED = "archived"

    state = models.CharField(max_length=10, choices=State, default=State.DRAFT)
```

### Pattern Matching Transitions

```python
TRANSITIONS = {("draft", "submit"): "submitted", ("submitted", "approve"): "approved",
               ("submitted", "reject"): "rejected", ("approved", "publish"): "published",
               ("archived", "publish"): "published", ("published", "archive"): "archived"}


def next_state(state, event):
    try:
        return TRANSITIONS[state, event]
    except KeyError as error:
        raise InvalidTransition(f"{event} from {state}") from error
```

### With Workflow Gem

```python
@transaction.atomic
def transition_post(*, post_id, event, actor):
    post = Post.objects.select_for_update().get(pk=post_id)
    authorize_transition(actor=actor, post=post, event=event)
    post.state = next_state(post.state, event)
    post.full_clean()
    post.save(update_fields=["state"])
    return post
```

### Standalone Workflow

When state machine isn't central to the model:

```python
@dataclass
class PublicationWorkflow:
    post: Post

    def submit(self):
        self.post.state = next_state(self.post.state, "submit")
        self.post.submitted_at = timezone.now()
# Save and lock in the operation, not implicitly when accessing this collaborator.
```

### Triggering Deliveries from Workflows

Workflows are an excellent place to trigger notifications - they keep side effects out of models while centralizing state-related behavior:

```python
@transaction.atomic
def finish_provisioning(*, cable_id):
    cable = Cable.objects.select_for_update().get(pk=cable_id)
    cable.mark_created()
    cable.save(update_fields=["status"])
    DeliveryIntent.objects.create(cable=cable, event="provisioned")
# A configured worker performs delivery after this intent becomes visible.
```

**Benefits:**
- Keeps models free of notification logic (no layer violation)
- Notifications tied to state transitions, not arbitrary callbacks
- Easy to see all side effects for a given state change
- Testable in isolation from the model

## Events Over Direct Transitions

```python
# Bad: bypasses transition guards.
Post.objects.filter(pk=post_id).update(state="published")
# Good: one explicit operation enforces the transition.
post = transition_post(post_id=post_id, event="publish", actor=actor)
```

## Transition Guards

```python
def publish(post):
    if not post.title or not post.body:
        raise InvalidTransition("Publication requires title and body")
    post.state = next_state(post.state, "publish")
```

## Transition Callbacks

```python
def approve(post, *, actor, at):
    post.state = next_state(post.state, "approve")
    post.reviewed_at = at
    post.reviewed_by = actor
# The operation saves and schedules notifications after commit.
```

## Anti-Patterns

### Implicit State Machines

```python
# One persisted state is authoritative; timestamps record transition history.
status = models.CharField(max_length=10, choices=Order.Status)
```

### Phantom Transitions

```python
# Repeating a disallowed transition raises; it must not send again.
with pytest.raises(InvalidTransition):
    next_state("published", "publish")
```

### Excessive Guards

```python
def approve_post(*, actor, post):
    if not ApprovalPolicy(actor, post).can_approve():
        raise PermissionDenied
    post.approve(by=actor)
```

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| workflow | Finite-state machine with introspection |
| workflow-activerecord | Django ORM integration |
| explicit collaborator construction | `explicit composition` for attaching workflows |
