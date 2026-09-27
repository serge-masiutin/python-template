# Configuration

## Contents

- Summary
- Layer Placement
- Key Principles
- Implementation with typed configuration
- Without typed configuration
- Testing Configuration
- Anti-Patterns
- File Organization
- Configuration Sources (Priority)

## Summary

Configuration management extracts settings from code into structured, environment-aware objects. Use frozen dataclasses for integration settings and explicit environment parsing at startup.

## Layer Placement

```
┌─────────────────────────────────────────┐
│ Domain Layer                            │
│  └─ Configuration classes (schema)      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Infrastructure Layer                    │
│  └─ Configuration sources               │
│     (ENV, YAML files, credentials)      │
└─────────────────────────────────────────┘
```

Configuration providers (ENV, YAML, credentials stores) are implementation details — infrastructure. By separating the schema from its data sources, config classes are promoted to the domain layer: upper layers depend on the typed config object, never on ENV/YAML directly.

## Key Principles

- **Explicit over implicit** — typed config classes, not scattered ENV reads
- **Fail fast** — validate configuration at boot
- **Environment-aware** — different values per environment
- **Testable** — override config in tests

## Implementation with typed configuration

### Basic Configuration

```python
@dataclass(frozen=True)
class PaymentsConfig:
    api_key: str
    webhook_secret: str
    currency: str

    @classmethod
    def from_environment(cls):
        config = cls(os.environ["PAYMENTS_API_KEY"], os.environ["PAYMENTS_WEBHOOK_SECRET"],
                     os.environ.get("PAYMENTS_CURRENCY", "USD"))
        if not config.api_key or not config.webhook_secret or config.currency not in {"USD", "EUR", "GBP"}:
            raise ValueError("Invalid payments configuration")
        return config
```

### Application Config Base

```python
# Construct once at the explicit startup boundary; pass the value to consumers.
payments_config = PaymentsConfig.from_environment()
```

### Usage

```python
def charge_order(*, order, provider, config):
    return provider.charge(amount=order.total_minor_units, currency=config.currency,
                           idempotency_key=str(order.pk))
```

### Nested Configuration

```python
@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int

@dataclass(frozen=True)
class EmailConfig:
    from_address: str
    smtp: SMTPConfig
```

### Feature Flags via Config

```python
@dataclass(frozen=True)
class FeaturesConfig:
    ai_summaries: bool = False

if config.ai_summaries:
    request_article_summary(article_id=article.pk)
```

### Validation

```python
def positive_integer(environment, name):
    value = int(environment[name])
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value
```

### Environment-Specific Behavior

```python
environment = os.environ["APP_ENV"]
if environment not in {"development", "test", "production"}:
    raise ValueError("Unknown environment")
force_https = environment == "production"
```

## Without typed configuration

### Simple Config Class

```python
# Prefer an explicit constructor over a hidden mutable singleton.
config = PaymentsConfig.from_environment()
processor = PaymentProcessor(config=config, client=client)
```

### Injected Secrets

```python
# Deployment injects secrets; required values fail at startup.
secret_key = os.environ["SECRET_KEY"]
```

## Testing Configuration

```python
def test_currency_from_environment(monkeypatch):
    monkeypatch.setenv("PAYMENTS_API_KEY", "test-key")
    monkeypatch.setenv("PAYMENTS_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("PAYMENTS_CURRENCY", "EUR")
    assert PaymentsConfig.from_environment().currency == "EUR"
```

## Anti-Patterns

### Scattered ENV Access

```python
# Bad: lower layers choose undocumented defaults and read global environment.
def charge(order):
    return provider.charge(order.total, currency=os.environ.get("CURRENCY", "USD"))
# Good: configuration is passed explicitly and already validated.
```

### Unvalidated Configuration

```python
@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int

    def __post_init__(self):
        if not self.host or not 1 <= self.port <= 65535:
            raise ValueError("Invalid SMTP host or port")
```

### Mutable Configuration

```python
@dataclass(frozen=True)
class AppConfig:
    api_key: str
# Do not mutate shared configuration during a request or test.
```

## File Organization

```
config/
├── application_config.py
├── database_config.py
├── email_config.py
├── features_config.py
└── stripe_config.py

config/
├── database.yml
├── email.yml
├── features.yml
└── stripe.yml
```

## Configuration Sources (Priority)

1. Production: injected environment variables.
2. Development: trusted `.env` sourced by `bin/manage`.
3. Explicit defaults in settings for genuinely optional values.

There is no implicit YAML or credential-store loader. Add one only for a concrete deployment requirement.

```python
# Precedence in this starter: bin/manage sources a trusted local .env;
# otherwise settings consume the injected process environment directly.
# Defaults are defined only in the configuration boundary.
```
