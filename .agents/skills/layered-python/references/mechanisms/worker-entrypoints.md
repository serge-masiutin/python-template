# Explicit Python Worker Entry Points

Adaptation of `explicit task delegation`: retain the audit for redundant model/job
wrappers, execution options, migration path and layer placement. Python does not
need runtime method generation to express a small task.

## When to Use

Review repeated enqueue wrappers, jobs with hidden domain logic and handlers whose
contracts are unclear. Thin tasks are legitimate: deserialization, execution scope,
logging and retry configuration are useful responsibilities even in a short wrapper.

## The Entry-Point Pattern

```python
def notify_recipients_job(*, post_id: int):
    post = Post.objects.get(pk=post_id)
    notify_recipients(post=post)
```

A configured backend calls this function. The template does not install a backend
or promise an `.enqueue`, `.delay` or `.perform_later` method on arbitrary functions.
Django's tasks API requires a backend that actually executes persisted work; merely
adding a task decorator is not a production worker.

### Short vs Configured Tasks

Use a plain domain function for synchronous work. Use the backend's explicit task
entrypoint for queued work and keep business behavior in the domain/operation.
Configuration belongs next to the task or in typed startup configuration.

## Detection Signals

- A model method exists solely to choose a queue.
- A decorator silently installs a second API or changes persistence behavior.
- Tasks accept entire ORM instances or an HTTP request.
- Retries can duplicate billing, notifications or other external effects.

## Configuration

Specify queue, attempts, timeout, cancellation and idempotency. Delayed execution
needs an explicit timestamp/timezone contract. Pass stable IDs and schema versions;
re-load current records in the worker. Define missing-record and revoked-access
behavior. Private method conventions are not an authorization boundary.

## Application-Wide Patterns

Do not patch `models.Model` to add implicit enqueue methods. Prefer a small callable
with explicit dependencies, and share a wrapper only when repetition demonstrates
a stable responsibility.

## When NOT to Use

Do not introduce a queue to remove a few wrapper lines. Keep an independent task
when it owns batching, execution policy, reconciliation or multiple callers.

## Migration Path

1. Inventory callers, serialized payloads, retries and queue names.
2. Extract domain work while preserving the old persisted-job entrypoint.
3. Test duplicate delivery, missing records and rollback.
4. Move callers to the new entrypoint; retire the old one after old jobs drain.

## Layer Placement

Tasks are internal inbound presentation boundaries. Operations own coordination;
models own invariants; queue adapters own transport. Use an atomic durable intent
when database change and delivery request must succeed together.
