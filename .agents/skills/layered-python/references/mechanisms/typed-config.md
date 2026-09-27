# Typed Python Configuration

Adaptation of typed configuration's schemas, sources, coercion, validation and test
isolation. Keep one explicit configuration boundary; do not reproduce Rails
credentials or singleton DSLs.

## Installation and Basic Usage

The standard library and Django settings are sufficient for the starter. Add a
settings library only when the existing schema requires it.

```python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class ProviderConfig:
    model: str
    timeout_seconds: float

    @classmethod
    def from_environment(cls):
        model = os.environ["PROVIDER_MODEL"]
        timeout = float(os.environ["PROVIDER_TIMEOUT_SECONDS"])
        if not model or timeout <= 0:
            raise ValueError("Provider model and positive timeout are required")
        return cls(model=model, timeout_seconds=timeout)
```

Construct configuration at startup. Ordinary consumers receive an immutable value
and access required fields directly.

## YAML Source and Nested Configuration

If a file source is necessary, parse it safely, validate its full schema at that
boundary and specify merge precedence. Do not treat nested arbitrary dictionaries
as validated configuration. Do not add a YAML dependency for this example alone.

## Base Config Class, Access and Type Coercion

Prefer focused dataclasses or existing Django settings. Parse booleans by accepted
literal values; `bool("false")` is true. Reject unknown enum values and out-of-range
limits. Keep defaults at the boundary and never catch a missing required secret to
replace it with an empty string.

## Environment Sources (Priority) and Local Overrides

Document every source and its precedence. This starter's `bin/manage` loads the
trusted local `.env` into process environment; deployment injects environment
variables directly. `.env` is ignored and created with restricted permissions.
Avoid changing process-global configuration at runtime or inside parallel tests.

## Testing

Use `monkeypatch.setenv` for an isolated configuration-parser test and
`override_settings` for framework behavior. Include malformed values, missing
required fields and valid optional defaults. Do not make tests depend on a real
provider key or the developer's environment.

## Secrets

Use the deployment secret store or injected environment. Never commit `.env`, copy
credentials into documentation or log a configuration object's full representation.
