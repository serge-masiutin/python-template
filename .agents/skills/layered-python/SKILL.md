---
name: layered-python
description: "Write, refactor and review Python/Django code using layered design: views, forms, models, operations, policies, queries, workers and explicit serializers. Includes specification tests, architecture audits, callback/god-object analysis and incremental refactoring workflows. Adapted from Layered Rails with native Python mechanisms."
metadata:
  version: "1"
  source: "serge-masiutin/rails-template@bc536d2f596d8f73daf2d59968221bf7315b5c94"
---

## Project Context

- Read `docs/architecture.md`, `pyproject.toml`, `uv.lock` and callers first. The starter
  uses Django, PostgreSQL, Inertia and React. Keep cohesive feature apps; conceptual
  layers do not require a directory or service class for every endpoint.
- Django views are HTTP controllers. Forms validate input; models own invariants;
  QuerySets own simple queries; explicit operations coordinate transactions.
- `save()` does not call `full_clean()`. `QuerySet.update()` and `bulk_create()` bypass
  model `save()` and save signals. Enforce concurrent invariants in the database.
- Prefer functions, dataclasses, explicit composition and native Django contracts.
  Do not reproduce Ruby DSLs, runtime method generation or a universal repository.
- Read [Python/Django sources](references/python-sources.md) for API details. Examples
  illustrate patterns; queues, AI SDKs, payment clients and uploads are not installed
  by this starter. Verify every concrete adapter before using it.
- This is a file-mapped adaptation of Vladimir Dementyev's Layered Rails material.
  The original archive, complete patch and source hashes are in the repository's
  `config/skills-lock.json` and `third_party/skills`.

# Layered Python

Design and review Django applications using layered architecture principles.

## Quick Start

Django applications are organized into four architecture layers with **unidirectional data flow**:

```
┌─────────────────────────────────────────┐
│           PRESENTATION LAYER            │
│   Controllers, Views, Channels, Jobs*   │
│ Forms, Filters, Presenters, Serializers │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           APPLICATION LAYER             │
│ Services, Policies, Mailers, Deliveries │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│             DOMAIN LAYER                │
│  Models, Value Objects, Query Objects   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          INFRASTRUCTURE LAYER           │
│  Django ORM, API Clients, Storage    │
└─────────────────────────────────────────┘
```

\* Jobs are **internal inbound** entry points: design-wise they follow the same rules as controllers, minus authentication and user-input handling.

**Core Rule:** Lower layers must never depend on higher layers.

See [Architecture Layers Reference](references/core/architecture-layers.md) for the full layer responsibilities and the Four Rules deep-dive.

## What this skill is for

Use this skill when:

1. **Analyzing a codebase** — apply the [architecture analysis](workflows/analyze.md) for a full audit, or zoom in with the [service-layer audit](workflows/analyze-services.md), [callback analysis](workflows/analyze-callbacks.md), or [god-object analysis](workflows/analyze-gods.md).
2. **Reviewing code changes** — run the [code review workflow](workflows/review.md) on a diff, file, or branch.
3. **Running the specification test** — use the [spec-test workflow](workflows/spec-test.md) on a single file or directory to evaluate whether code belongs in its current layer.
4. **Planning gradual adoption** — generate a phased roadmap with the [layerification plan workflow](workflows/plan.md), focused on a goal like "introduce authorization" or "decompose god objects."
5. **Planning a feature** — I'll apply the layered principles below to whichever code you're about to write.
6. **Implementing a specific pattern** — authorization, notifications, view components, AI integration, etc. — see the Pattern Catalog and Topic References below.

Invoke the linked workflows directly or request them in natural language. This
repository does not ship the original Rails slash-command plugin.

## Workflows

Reusable procedures bundled inside this skill. Read the file and apply it to the target code:

- [Architecture analysis](workflows/analyze.md) — full layered-architecture audit of a Django codebase
- [Code review](workflows/review.md) — review a diff or file set for layer violations
- [Specification test](workflows/spec-test.md) — evaluate whether code belongs in its current layer
- [Service-layer audit](workflows/analyze-services.md) — deep audit of `<feature>/operations/` and service-like classes (per-cluster proposals, contracts, layer hygiene)
- [Callback analysis](workflows/analyze-callbacks.md) — score Django ORM callbacks and find extraction candidates
- [God-object analysis](workflows/analyze-gods.md) — identify oversized models and recommend decomposition
- [Gradual layerification plan](workflows/plan.md) — incremental roadmap for adopting layered patterns
- [Import boundary checks](workflows/archspec.md) — verify concrete forbidden import edges in CI

## Core Principles

### The Four Rules

1. **Unidirectional Data Flow** - Data flows top-to-bottom only
2. **No Reverse Dependencies** - Lower layers never depend on higher layers
3. **Abstraction Boundaries** - Each abstraction belongs to exactly one layer
4. **Minimize Connections** - Fewer inter-layer connections = looser coupling

### Common Violations

| Violation | Example | Fix |
|-----------|---------|-----|
| Model uses ambient context | `ambient_actor` in model | Pass user as explicit parameter |
| Service accepts request | `request: HttpRequest` in service | Extract value object from request |
| Controller has business logic | Pricing calculations in action | Extract to service or model |
| Anemic models | All logic in services | Keep domain logic in models |

| Category | Reference |
|----------|-----------|
| Layer violations (Ambient context in models, request in services, notifications in models, business logic in controllers) | [layer-violations.md](references/anti-patterns/layer-violations.md) |
| Service objects (anemic models, bag of random objects, premature abstraction) | [service-objects.md](references/anti-patterns/service-objects.md) |
| Callbacks (operation callbacks, skip callbacks, control flags) | [callbacks.md](references/anti-patterns/callbacks.md) |
| Concerns (code-slicing, overgrown) | [concerns.md](references/anti-patterns/concerns.md) |
| Helpers (HTML construction in helpers) | [helpers.md](references/anti-patterns/helpers.md) |
| Jobs (anemic jobs) | [jobs.md](references/anti-patterns/jobs.md) |
| Testing (testing wrong layer) | [testing.md](references/anti-patterns/testing.md) |

### The Specification Test

> If the specification of an object describes features beyond the primary responsibility of its abstraction layer, such features should be extracted into lower layers.

**How to apply:**
1. List responsibilities the code handles
2. Evaluate each against the layer's primary concern
3. Extract misplaced responsibilities to appropriate layers

See [Specification Test Reference](references/core/specification-test.md) for detailed guide.

## Pattern Catalog

| Pattern | Layer | Use When | Reference |
|---------|-------|----------|-----------|
| Service Object | Application | Orchestrating domain operations | [service-objects.md](references/patterns/service-objects.md) |
| Query Object | Domain | Complex, reusable queries | [query-objects.md](references/patterns/query-objects.md) |
| Form Object | Presentation | Multi-model forms, complex validation | [form-objects.md](references/patterns/form-objects.md) |
| Filter Object | Presentation | Request parameter transformation | [filter-objects.md](references/patterns/filter-objects.md) |
| Presenter | Presentation | View-specific logic, multiple models | [presenters.md](references/patterns/presenters.md) |
| Serializer | Presentation | API response formatting | [serializers.md](references/patterns/serializers.md) |
| Policy Object | Application | Authorization decisions | [policy-objects.md](references/patterns/policy-objects.md) |
| Value Object | Domain | Immutable, identity-less concepts | [value-objects.md](references/patterns/value-objects.md) |
| Collaborator Object | Domain | A slice of one model's behavior in a typed delegate | [collaborator-objects.md](references/patterns/collaborator-objects.md) |
| State Machine | Domain | States, events, transitions | [state-machines.md](references/patterns/state-machines.md) |
| Concern | Domain | Shared behavioral extraction | [concerns.md](references/patterns/concerns.md) |
| Repository | Domain | **Last resort** — returning custom domain objects mapped from ORM data, after QuerySet methods (simple) and query objects (query building) are insufficient | [repositories.md](references/patterns/repositories.md) |

### Pattern Selection Guide

**"Where should this code go?"**

| If you have... | Consider... |
|----------------|-------------|
| Complex multi-model form | Form Object |
| Request parameter filtering/transformation | Filter Object |
| View-specific formatting | Presenter |
| Complex database query used in multiple places | Query Object |
| Business operation spanning multiple models | Service Object (as waiting room) |
| Authorization rules | Policy Object |
| Multi-channel notifications | Delivery Object (explicit delivery) |

**Remember:** Services are a "waiting room" for code until proper abstractions emerge. Don't let `app/services` become a bag of random objects.

## Refactoring Scenarios

Canonical before/after transformations for the most common layerification moves. The [layerification plan workflow](workflows/plan.md) uses these as reference templates when proposing phases.

| Scenario | Goal area | Reference |
|----------|-----------|-----------|
| Extract callbacks to service | callbacks, post_save receiver chains | [callbacks-to-service.md](examples/callbacks-to-service.md) |
| Extract authorization to policy | authorization, permissions | [authorization-to-policy.md](examples/authorization-to-policy.md) |
| Extract query logic to query object | complex scopes, reporting queries | [query-to-query-object.md](examples/query-to-query-object.md) |
| Extract Current from model | ambient context in domain | [current-from-model.md](examples/current-from-model.md) |
| Decompose god object with associated objects | god model, large User/Account | [god-object-decomposition.md](examples/god-object-decomposition.md) |
| Replace implicit state machine | timestamp-based status | [implicit-to-explicit-state-machine.md](examples/implicit-to-explicit-state-machine.md) |
| Extract view logic to presenter | template logic, formatting | [view-logic-to-presenter.md](examples/view-logic-to-presenter.md) |
| Form object for complex input | fat controllers, multi-model forms | [complex-input-to-form-object.md](examples/complex-input-to-form-object.md) |

## Topic References

For deep dives on specific topics:

| Topic | Reference |
|-------|-----------|
| Authorization (RBAC, ABAC, policies) | [authorization.md](references/topics/authorization.md) |
| Notifications (multi-channel delivery) | [notifications.md](references/topics/notifications.md) |
| View Components | [view-components.md](references/topics/view-components.md) |
| AI Integration (LLM, agents, RAG, MCP) | [ai-integration.md](references/topics/ai-integration.md) |
| Configuration | [configuration.md](references/topics/configuration.md) |
| Callbacks (scoring, extraction) | [callbacks.md](references/topics/callbacks.md) |
| Current Attributes | [current-attributes.md](references/topics/current-attributes.md) |
| Instrumentation (logging, metrics) | [instrumentation.md](references/topics/instrumentation.md) |

## Python Mechanism References

| Mechanism | Purpose | Reference |
|---|---|---|
| Django permissions and policies | Explicit authorization | [Policies](references/mechanisms/django-policies.md) |
| React components | Typed presentation | [Components](references/mechanisms/react-components.md) |
| Settings and dataclasses | Validated configuration | [Configuration](references/mechanisms/typed-config.md) |
| Explicit delivery functions | Notifications and commit boundaries | [Delivery](references/mechanisms/django-delivery.md) |
| DTO functions | Allowlisted JSON | [Serialization](references/mechanisms/explicit-json.md) |
| Explicit transitions | State machines | [Transitions](references/mechanisms/explicit-state-machines.md) |
| Forms and QuerySets | Validated filters | [Filters](references/mechanisms/django-filters.md) |
| Provider adapters | AI boundary | [AI](references/mechanisms/ai-provider-boundary.md) |
| Explicit worker functions | Queue entrypoints | [Workers](references/mechanisms/worker-entrypoints.md) |
| Import checks | Enforce selected dependency boundaries | [Imports](references/mechanisms/import-boundaries.md) |

## Extraction Signals

**When to extract from models:**

| Signal | Metric | Action |
|--------|--------|--------|
| God object | High churn × complexity | Decompose into concerns, delegates, or separate models |
| Operation callback | Score 1-2/5 | Extract to service or event handler |
| Code-slicing concern | Groups by artifact type | Convert to behavioral concern or extract |
| Ambient context dependency | Model reads ambient context | Pass as explicit parameter |

**Callback Scoring:**
| Type | Score | Keep? |
|------|-------|-------|
| Transformer (compute values) | 5/5 | Yes |
| Normalizer (sanitize input) | 4/5 | Yes |
| Utility (counter caches) | 4/5 | Yes |
| Observer (side effects) | 2/5 | Maybe |
| Operation (business steps) | 1/5 | Extract |

See [Extraction Signals Reference](references/core/extraction-signals.md) for detailed guide.

## Model Organization

Recommended order within model files:

```python
class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(published_at__isnull=False)


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    published_at = models.DateTimeField(null=True)
    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-pk"]

    def publish(self, *, at):
        if self.published_at is not None:
            raise InvalidTransition("Post is already published")
        self.published_at = at
# The operation validates, saves, and records any external-delivery intent.
```

## Success Checklist

Well-layered code:

- [ ] No reverse dependencies (lower layers don't depend on higher)
- [ ] Models don't access Current attributes
- [ ] Services don't accept request objects
- [ ] Controllers are thin (HTTP concerns only)
- [ ] Domain logic lives in models, not services
- [ ] Callbacks score 4+ or are extracted
- [ ] Concerns are behavioral, not code-slicing
- [ ] Abstractions don't span multiple layers
- [ ] Tests verify appropriate layer responsibilities

## Guidelines

- **Use domain language** - Name models after business concepts (Participant, not User; Cloud, not GeneratedImage)
- **Patterns before abstractions** - Let code age before extracting; premature abstraction is worse than duplication
- **Services as waiting room** - Don't let `app/services` become permanent residence for code
- **Explicit over implicit** - Prefer explicit parameters over Current attributes
- **Extraction thresholds** - Consider extraction when methods exceed 15 lines or call external APIs
