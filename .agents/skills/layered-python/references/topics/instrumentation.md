# Instrumentation

## Contents

- Summary
- Layer Placement
- Key Principles
- Python Logging and Explicit Instrumentation
- Structured Logging
- Metrics
- Service Instrumentation
- Anti-Patterns
- Testing Instrumentation
- Performance Considerations

## Summary

Instrumentation provides visibility into application behavior through logging, metrics, and tracing. It's an infrastructure concern that should be non-invasive to domain logic.

## Layer Placement

```
┌─────────────────────────────────────────┐
│ Infrastructure Layer                    │
│  └─ Instrumentation subscribers         │
│  └─ Log formatters                      │
│  └─ Metrics collectors                  │
└─────────────────────────────────────────┘
```

## Key Principles

- **Non-invasive** — domain code shouldn't know about instrumentation
- **Event-driven** — emit bounded structured events through logging or the configured tracing backend
- **Structured** — use tagged/structured logging
- **Centralized** — configure in initializers, not throughout code

## Python Logging and Explicit Instrumentation

### Subscribe to Events

```python
started = time.perf_counter()
response = get_response(request)
logger.info("http_request", extra={"status_code": response.status_code,
            "duration_ms": (time.perf_counter() - started) * 1000})
# Log route names, not raw query strings or user-controlled paths.
```

### Custom Events

```python
started = time.perf_counter()
result = gateway.charge(order=order)
metrics.observe_payment(time.perf_counter() - started, status=result.status)
# metrics is the application's explicit adapter, with bounded status values.
```

### LogSubscriber Pattern

```python
logger.info("payment_completed", extra={"status": result.status, "duration_ms": elapsed_ms})
# Exclude private payment details and provider response bodies.
```

## Structured Logging

### Tagged Logging

```python
logger = logging.LoggerAdapter(logging.getLogger(__name__), {"request_id": request_id})
logger.info("request_completed")
```

### JSON Logging

```python
class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"level": record.levelname, "event": record.getMessage(),
                           "time": datetime.fromtimestamp(record.created, UTC).isoformat()})
# Configure centrally; add only reviewed fields and a deliberate error representation.
```

### Semantic Logger

```python
try:
    result = payment_gateway.charge(order=order)
except PaymentTimeout:
    logger.exception("payment_timeout")
    raise
# Redact sensitive exception content in the provider adapter before logging.
```

## Metrics

### StatsD Integration

```python
# Configure the selected metrics backend at startup, not in a global connection.
metrics.observe_http(route="notes-create", status=201, seconds=elapsed)
# Never use user IDs, prompts or full URLs as metric labels.
```

### Custom Metrics

```python
metrics.increment("users_created")
metrics.observe_payment(seconds=elapsed, status="success")
# Backend integration is illustrative; no metrics client is installed by the starter.
```

## Service Instrumentation

### Instrumented Base Class

```python
@contextmanager
def timed_operation(name, metrics):
    started = time.perf_counter()
    try:
        yield
    finally:
        metrics.observe_duration(name, time.perf_counter() - started)
# The metric name is a bounded constant chosen by the caller.
```

### Manual Instrumentation

```python
with timed_operation("import_records", metrics):
    result = import_records(source)
logger.info("import_completed", extra={"record_count": len(result)})
```

## Anti-Patterns

### Logging in Domain Models

```python
# Observe at the entry point or operation boundary; no logging-only model signal.
order = place_order(actor=actor, items=items)
logger.info("order_created")
```

### Metrics Scattered in Code

```python
with timed_operation("process_payment", metrics):
    result = process_payment(order=order, gateway=gateway)
# Keep domain calculations independent of the telemetry backend.
```

### Verbose Debug Logging

```python
with timed_operation("process_batch", metrics):
    results = [transform(item) for item in items]
logger.info("batch_completed", extra={"record_count": len(results)})
```

## Testing Instrumentation

```python
def test_operation_records_duration(metrics):
    with timed_operation("process_payment", metrics):
        calculate_total(items)
    metrics.observe_duration.assert_called_once()
    assert metrics.observe_duration.call_args.args[0] == "process_payment"
```

## Performance Considerations

```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("diagnostic_counts=%s", expensive_safe_counts())
# Sample high-volume telemetry only under a measured, explicit policy.
# Never sample away errors needed to diagnose failed operations.
```
