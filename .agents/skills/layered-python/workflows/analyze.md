# Architecture Analysis Workflow

Comprehensive layered architecture analysis of a Django codebase or specific directory. Evaluates how well the codebase follows layered architecture principles, identifying:
- Layer violations
- Abstraction opportunities
- God objects
- Callback concerns
- Missing patterns

## Contents

- [Analysis Process](#analysis-process)
- [Reporting Principles](#reporting-principles)
- [Output Format](#output-format)
- [Severity Levels](#severity-levels)

## Analysis Process

### 1. Structural Assessment

Map existing code to layers:

```
Presentation Layer:
  - <feature>/views/
  - app/views/
  - web/components/
  - <feature>/presentation/
  - <feature>/presentation/
  - app/serializers/
  - <feature>/forms/
  - app/filters/
  - app/channels/
  - <feature>/tasks/        # internal inbound — same design rules as controllers,
                     # minus authentication and user-input handling

Application Layer:
  - <feature>/operations/
  - <feature>/operations/
  - <feature>/policies/
  - app/mailers/
  - <feature>/delivery/
  - <feature>/delivery/

Domain Layer:
  - <feature>/models/
  - <feature>/queries/
  - app/values/
  - config/     # config schema objects; their sources (ENV/YAML/credentials)
                     # are infrastructure

Infrastructure Layer:
  - <feature>/integrations/
  - queue/storage/delivery adapters (usually mechanisms, not app code)
```

Record existing import-boundary tests or configuration. Recommend a focused check only for a demonstrated boundary risk; follow [the import-boundary workflow](archspec.md).

**Service Layer Brief** (when `<feature>/operations/` exists OR `<feature>/models/` shows service-like classes):

This sub-step runs a *lite version* of the service-layer audit and produces a single short section in the final report (see Output Format → "## Service Layer Brief"). The brief stays under ~25 lines; it does not include per-cluster proposal blocks, contracts, current-pain prose, or test-win paragraphs — those live in the dedicated service-layer audit. **Recommend running the service-layer audit (`analyze-services` workflow) whenever the brief surfaces a non-trivial finding.**

What to compute, in order:

1. **Waiting-room gate.** Count files and LOC under `<feature>/operations/`; compute service share of `app/`. If `service_count < 10` OR `service_share < 0.10`, set tier to `Waiting room (gate fired)` and skip cluster detection — but still scan `<feature>/models/` for service-like classes (next step).

2. **Empirical mirror — one sentence.** Sample 5–10 representative service files (most-recently-modified + largest + a few short ones) and synthesize the team's implicit design pattern for a service: class shape, call interface, parameter style, return shape. The brief reports exactly **one sentence**, no code or numbers. Even when no convention has emerged, name the pattern that has: *"any Python callable placed under `<feature>/operations/`"* is a definition. Never write "not defined".

3. **Hidden services in `<feature>/models/`.** Scan for non-model classes with action interfaces and service-like names (`*_service`, `*_command`, `*_sync`, `*_importer`, `*_processor`, `*_notifier`, `*_calculator`, `*_resolver`, `*_query`, `*_finder`). Classify each as **domain** (calculators, queries, resolvers — pure derivation from domain data) or **application** (notifiers, syncs, importers — orchestrate side effects).

4. **Architecture tier.** Pick one:
   - **Mature decomposition** — `<feature>/operations/` is small (gate fires) AND ≥3 specialization folders exist (`forms/`, `queries/`, `policies/`, `deliveries/`, `presenters/`, `operations/`).
   - **Mature decomposition (models-first variant)** — `<feature>/operations/` intentionally absent AND deep model namespacing carries the orchestration.
   - **Mixed** — some specializations promoted, others still in services.
   - **Pre-decomposition** — `<feature>/operations/` is large AND zero specialization folders.

5. **Convention strength — one word per axis, no percentages in the brief.** For base class, call interface, parameter style, naming suffix/form, return value: classify as Strong / Mixed / Weak. Roll up into a single overall verdict (Strong / Mixed / Weak / "bag of random objects").

6. **Cluster headlines — top 3 only.** Tokenize service basenames; group by suffix/prefix. Surface the three largest clusters as one-liners: `<pattern> (N services) — <promote candidate / demote candidate / strong cluster / borderline>`. **No proposal blocks in the brief.** If the codebase has a clearly *healthy* cluster (shared base, single deferral surface, infra separated), name it as the **healthy reference** so the team has an anchor.

7. **Specialization folder verdicts.** For each of `<feature>/forms/`, `<feature>/queries/`, `<feature>/policies/`, `<feature>/delivery/`, `<feature>/delivery/`, `<feature>/presentation/`, `web/components/`, `<feature>/operations/`, `<feature>/integrations/`: emit ✓ healthy / ⚠ ghost (folder exists but <3 files OR no base OR same-shape candidates hidden elsewhere) / ✗ absent. Ghosts are more actionable than absences — flag them.

8. **Cross-cutting smell counts.** One line each, with counts only:
   - Naming smells (`-er` suspects, tautological pairs, scheduling-frequency names) — count.
   - Layer-hygiene issues (`request`/`params`/`flash`/`render` in services, authorization leaks) — count.
   - Implicit-workflow chains of length ≥3 — count.
   - Misplaced code (non-services, mixed-layer files, console/CLI utilities) — count.

9. **Anemic-model risk.** Count models heavily referenced from services that have <3 substantive instance methods. A non-zero count flips the brief's diagnosis from "promote services" to "the domain is too thin."

**Scoring guidance:**

- Never label a large service directory (100+ files) as "Strong" or "Excellent" without verifying organization. A flat `<feature>/operations/` with 200+ files is a red flag regardless of count.
- A well-namespaced service layer with clear decomposition patterns can be healthy even at high counts.
- The brief must stay short. If any of the per-cluster proposals would take >2 lines to summarize honestly, that's the signal to defer to the service-layer audit — not to inline a longer brief.
- The brief always closes with: *"For per-cluster proposals (contracts, current pain, test wins, placement options), run the analyze-services workflow."*

For the full audit framework — empirical-mirror rationale, classification rules, cluster proposal blocks, and the reporting principles that govern the headline content — see the analyze-services workflow.

### 2. Layer Violation Detection

Search for common violations:

**Upward Dependencies in Models**

Search for ALL types of upward-layer invocations from models:

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "ContextVar|threading.local|request\.|HttpRequest|render\(|redirect\(" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

**Only include in report if violations are found.** Omit this section entirely if no upward dependencies exist in models.

**Ambient context in Models**

Search for ContextVar, threading.local and request globals, then classify usage:

- **Acceptable:** observability metadata restored with reset(token) in finally;
  scoped Django locale/time-zone overrides at the presentation boundary.
- **Concerning:** actor, tenant, audit owner, permission decisions and query scoping
  read implicitly. Pass authorized actor/tenant explicitly; defaults in Python
  function signatures are evaluated at definition time, not per request.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "ContextVar|threading.local|request\.|HttpRequest|render\(|redirect\(" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

**Reporting rules:**
- If only acceptable patterns found → mention briefly: "Current usage follows acceptable patterns (AR defaults, audit logging)"
- If concerning patterns found → report those specifically as violations
- If no Current usage → omit entirely

See [Current Attributes](../references/topics/current-attributes.md) for the full "Where Current IS Appropriate" table.

**Request Objects in Services**
```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "ContextVar|threading.local|request\.|HttpRequest|render\(|redirect\(" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

**Business Logic in Controllers**
```python
# Look for entry points with domain calculations, multiple model owners,
# implicit effects and unvalidated boundary input; trace actual callers.
```

**Authorization in Models**
```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "ContextVar|threading.local|request\.|HttpRequest|render\(|redirect\(" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

For each violation found:
1. Trace the call chain (who calls this code?)
2. Find existing orchestrators (services, forms, controllers)
3. Recommend moving side effects to the orchestrator
4. If no orchestrator exists, list options (service, form, controller)

### 3. God Object Identification

Using churn × complexity heuristic:

```bash
git log --format= --name-only --since="6 months ago" -- "*.py"
```

Candidates scoring high on both metrics are god object suspects.

### 4. Callback Analysis

Score all callbacks in models:

| Score | Assessment |
|-------|------------|
| 5/5 | Transformer - keep |
| 4/5 | Maintainer - keep |
| 3/5 | Timestamp - acceptable |
| 2/5 | Background trigger - consider extracting |
| 1/5 | Operation - should extract |

### 5. Coupling Analysis via Specification Test

Apply the [specification test](../references/core/specification-test.md) to the top 3-5 suspicious entities identified during analysis:

**Pick candidates from:**
- Controllers with complex actions (business logic detected in Step 2)
- Jobs with non-trivial logic (more than delegation)
- Large services (high line count or many dependencies)
- Models with mixed-layer responsibilities

**For each candidate:**

1. List every responsibility the entity handles
2. Categorize each responsibility by layer (Presentation / Application / Domain / Infrastructure)
3. Identify misplaced responsibilities — anything outside the entity's primary layer

**Report format:**

```
Entity: OrdersController#create
  - Parse parameters         → Presentation ✓
  - Authenticate user        → Presentation ✓
  - Validate inventory       → Domain ✗ (extract to model)
  - Calculate pricing        → Domain ✗ (extract to model)
  - Send confirmation email  → Infrastructure ✗ (extract to service)
  Recommendation: Extract domain logic to Order model, orchestrate via CreateOrderService
```

Keep this focused — apply to the most suspicious entities only, not exhaustively. Omit this section if no candidates warrant the specification test.

### 6. Concern Health Check

For each concern, verify:
- [ ] Used by multiple models (not single-model organization)
- [ ] Methods are cohesively related
- [ ] No hidden dependencies on including class
- [ ] Doesn't recreate callback problems

### 7. Anti-Pattern Detection

Check for common anti-patterns. The SKILL.md "Common Violations" table groups them by category and links to detailed references — consult it for the full taxonomy.

**Anemic Jobs**
```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "transaction.atomic|on_commit|def .*task|urllib|requests|httpx|openai|anthropic|send_mail" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Signal: a worker adds duplicate orchestration without a queue-boundary responsibility. A thin worker is healthy when it owns serialization, retries or execution context. Keep explicit delegation; do not generate model task methods.

**Helper HTML Construction**
```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def |dataclass|Protocol" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Signal: Heavy `tag.div`, `tag.button` chains. Fix: Extract to React component.

**Callback Control Flags**
```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Signal: Virtual attributes to bypass callbacks. Fix: Extract callbacks to explicit service calls.

For each anti-pattern, reference the specific fix in the anti-patterns documentation.

### 8. Pattern Gap Analysis

Identify missing abstractions:

- **No policies?** Check for authorization in controllers/models
- **No form objects?** Check for complex params handling
- **No query objects?** Check for long scope chains
- **No presenters?** Check for view logic in models

## Reporting Principles

**Conditional reporting:** Only include a section in the report if there are meaningful findings. Do not report "No violations found" for every check — omit empty sections entirely. Focus the report on what matters for this specific codebase.

## Output Format

```markdown
# Layered Architecture Analysis

## Summary
- Overall health: [Good/Fair/Needs Attention/Critical]
- Layer compliance: [percentage]
- God object candidates: [count]
- Callback concerns: [count]
- Anti-patterns detected: [count]
- Service layer tier: [Mature decomposition | Mature decomposition (models-first) | Mixed | Pre-decomposition | Waiting room]

## Service Layer Brief

**In this project, a Service Object is:** <one sentence — the empirical mirror>

- **Architecture tier:** Mature decomposition | Mature decomposition (models-first variant) | Mixed | Pre-decomposition | Waiting room
- **Convention strength:** Strong | Mixed | Weak (bag of random objects)
- **Specialization folders:** forms ✓ | queries ⚠ ghost (2 files, no base) | policies ✓ | deliveries ✗ | presenters ✗
- **Top clusters (3):**
  1. `*Importer` (8 services) — promote candidate
  2. `*Notifier` (6 services) — strong cluster, healthy reference
  3. `*Processor` (4 services) — borderline; watch for premature consolidation
- **Hidden in `<feature>/models/`:** N service-like classes (D domain candidates / A application leaks)
- **Cross-cutting smells:** K naming, M layer-hygiene, J implicit workflows, P misplaced
- **Anemic-model risk:** Q models with <3 substantive methods

> For per-cluster proposals (contracts, current pain, test wins, placement options), run the analyze-services workflow.

Omit any bullet whose finding is zero. Skip the entire section only when `<feature>/operations/` is intentionally absent AND the `<feature>/models/` scan finds no application-layer leaks AND no demote candidates — in which case the Summary's tier line carries the verdict.

## Layer Violations

### Critical
1. `<feature>/models/user.py:45` - `ambient_actor.is_staff` used for business logic decision
   - Impact: Domain coupled to request context for authorization
   - Fix: Move to policy object or pass user explicitly through service layer

### Major
...

### Minor
...

## God Object Candidates

| Model | Lines | Churn | Complexity | Recommendation |
|-------|-------|-------|------------|----------------|
| User | 450 | High | High | Extract concerns, services |
| Order | 380 | Medium | High | State machine, form objects |

## Callback Concerns

| File | Callback | Score | Recommendation |
|------|----------|-------|----------------|
| user.py | post_save receiver :send_welcome | 1/5 | Extract to service |
| post.py | pre_save receiver :update_slug | 5/5 | Keep |

## Anti-Patterns

| Type | Location | Fix |
|------|----------|-----|
| Anemic Job | `NotifyRecipientsJob` | Keep explicit queue entrypoint |
| Helper HTML | `messages_helper.py` | Extract to React component |

The SKILL.md "Common Violations" section has the per-category references.

## Pattern Recommendations

### Immediate Actions
1. Extract `User` authentication logic to `AuthenticateUser` service
2. Move `Order.can_cancel` authorization to `OrderPolicy`
3. Replace `Post` callbacks with `PublishPost` service

### Future Improvements
1. Add form objects for multi-model forms
2. Consider query objects for reporting
3. Extract view logic to presenters
```

## Severity Levels

### Critical
- Domain layer using Current for business logic, authorization, or query building
- Circular dependencies between layers
- Business logic in views

### Major
- Heavy callback chains (5+ callbacks)
- God objects (>300 lines, high churn)
- Authorization scattered across layers
- Callback control flags (`skip_*` attributes)

### Minor
- Missing abstractions (could benefit from patterns)
- Concerns used by single model
- Overly complex scopes
- Anemic jobs (single-delegation wrappers)
- Helper HTML construction (candidates for React components)
