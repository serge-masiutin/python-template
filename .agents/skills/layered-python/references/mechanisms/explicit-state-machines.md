# Explicit State Machines in Python

Adaptation of Workflow's states, events, guards, transition effects, standalone
workflows and tests. Start with enums/choices and explicit methods; no state-machine
dependency is installed.

## Installation and Basic Usage

```python
class PublicationState(models.TextChoices):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PUBLISHED = "published"

TRANSITIONS = {
    ("draft", "submit"): "submitted",
    ("submitted", "approve"): "approved",
    ("approved", "publish"): "published",
}

def next_state(state, event):
    try:
        return TRANSITIONS[state, event]
    except KeyError as error:
        raise InvalidTransition(f"Cannot {event} from {state}") from error
```

### Trigger Transitions and Check Available Events

The operation loads the record under `transaction.atomic()` with
`select_for_update()`, checks access, applies the domain transition and saves. An
optimistic conditional update is another valid concurrency contract. `choices`
helps forms but does not create a database constraint; add one for stored states.

## Per-Event Methods and Guards

A transition method updates state and audit timestamps using an explicit actor/time.
Guard domain preconditions there; enforce role/tenant access at the chosen application
boundary. Never read an ambient request or send email from a state property.

## State-Dependent Behavior and Standalone Workflow

Extract a collaborator when a state graph is a coherent independent responsibility.
Keep it composed with the domain object. Do not create a workflow base class or
runtime-generated methods before the graph requires them.

## Generic Transition Hooks

Prefer an explicit operation over a generic callback. Persist event/delivery intent
atomically when required; external calls occur after commit in a worker. A transition
must not report success when the write failed. A repeated completed command needs a
specified no-op/error response and must not duplicate external effects.

## Querying by State

```python
published = Post.objects.filter(state=PublicationState.PUBLISHED)
```

Use the same authoritative state field for queries and guards. Historical timestamps
are evidence, not a second competing state machine.

## Testing

Cover every allowed edge, illegal transitions, missing permissions, duplicate commands,
rollback and concurrent attempts. PostgreSQL transaction tests must demonstrate locks
or conditional updates; SQLite cannot prove row-lock semantics.
