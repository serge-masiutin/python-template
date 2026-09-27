---
lint-skip:
  - rule: reference.one-level-deep
    reason: "Review workflow defers service classification to the service-layer audit workflow; the deep-link anchors (Phase 2.2, §3.6.x) are the authoritative procedure being delegated to, and routing them through SKILL.md would lose precision and indirection users would have to chase."
---

# Layered Python Review Workflow

Code review applying layered architecture principles to Django diffs, files, or branches.

## Contents

- [Philosophy](#philosophy)
- [Process](#process)
- [Review Principles](#review-principles)
- [Review Checklist](#review-checklist)
- [Resolving Violations](#resolving-violations)
- [Reviewing Test Files](#reviewing-test-files)
- [Output Format](#output-format)
- [Severity Levels](#severity-levels)
- [Example Review](#example-review)
- [Related](#related)

## Philosophy

This review evaluates code against the principles from "Layered Design for Ruby on Rails Applications":

- **Favor extraction over complication** — when code grows complex, extract to the appropriate layer
- **Patterns before abstractions** — let code age before extracting; premature abstraction is worse than duplication
- **Services as waiting room** — `app/services` is temporary residence until proper abstractions emerge
- **Domain logic stays in models** — avoid anemic models; services orchestrate, models know business rules
- **Explicit over implicit** — prefer explicit parameters over Current attributes
- **Lower layers never depend on higher layers** — no reverse dependencies

## Process

1. **Identify changed files** (from git diff or provided paths)
2. **Determine layers touched** by the changes
3. **Apply layer boundary checks**
   - Grep for `ambient context` in models
   - Check service parameters for request/params objects
   - Look for business logic in controllers
4. **Apply the service-layer audit's classification rules** when the diff touches:
   - `<feature>/operations/`, `<feature>/ai/`, `<feature>/integrations/`, `<feature>/operations/`, `<feature>/delivery/`, or other application-layer specializations
   - Any **new non-model class under `<feature>/models/`** (service-shaped Python objects, `*Extractor`/`*Suggester`/`*Writer`/`*Checker`/`*Merger`/`*Filler`/`*Enricher` files), or
   - HTTP/SDK/LLM SDK calls anywhere in the diff (`the installed LLM SDK`, `OpenAI`, `Anthropic`, `Stripe.`, `urllib.request`, `configured_channel_layer.group_send`, etc.)

   For each such file, run the [service-layer audit's classification rule (Phase 2.2, "purpose first, regex second")](analyze-services.md#22-cluster-classification-promote-vs-demote) and the misplaced-code checks (§3.6.1–§3.6.5). Do **not** improvise a classification from layered-rails principles alone — the audit is the authority. In particular:

   - **LLM/AI SDK calls** are not domain calculators; they're agent-layer (§3.6.5 + Phase 2.1 cluster table → `<feature>/ai/`).
   - **Non-AR class under `<feature>/models/` that wraps HTTP/SDK/broadcast** → promote to `<feature>/operations/` or a specialization layer (§3.6.4). The `<feature>/operations/` self-separation gate (§3.6.1) does **not** apply.
   - **Thin SDK/broadcast wrappers** with no value-add → delete or hoist to a concern (§3.6.5). Verify with the SDK's docs whether the wrapper adds anything the SDK already provides.
   - **"Models-first" is not a permission slip.** A single application-shaped class under `<feature>/models/` makes the verdict **Mixed**, not "Mature decomposition (models-first variant)". Recommend introducing `<feature>/operations/` for the leaks — see Phase 1.3's decision gate and "What 'models-first' actually means".
5. **Run the [specification test](../references/core/specification-test.md)** on key files
6. **Check for extraction signals**
   - Score callbacks
   - Assess concern health
   - Check god-object indicators
7. **Generate review report** with prioritized issues

## Review Principles

### 1. Layer Boundary Enforcement

Check for violations of the four architecture rules:

- **No reverse dependencies** — models don't use Current; services don't accept request objects
- **Abstraction boundaries** — each abstraction belongs to exactly one layer
- **Unidirectional data flow** — data flows top-to-bottom only
- **Minimal connections** — avoid unnecessary coupling between layers

**Flag:**
- `ambient context` usage in models
- Request/params objects passed to services
- Mailers called from model callbacks
- SQL queries in controllers
- Business calculations in views

### 2. Specification Test Application

Evaluate whether code responsibilities match the layer:

- **Controllers** should only handle HTTP concerns (auth, params, response)
- **Services** should orchestrate domain objects, not contain domain logic
- **Models** should contain business rules and domain logic
- **Views** should only format data for display

**Ask:**
- Would testing this require HTTP setup when it shouldn't?
- Is this test verifying the right layer's responsibility?
- Could this logic be tested with a simpler, lower-layer test?

### 3. Extraction Signal Detection

Identify code that should be extracted:

**Callback scoring:**
| Type | Score | Action |
|------|-------|--------|
| Transformer (compute values) | 5/5 | Keep |
| Normalizer (sanitize input) | 4/5 | Keep |
| Utility (counter caches) | 4/5 | Keep |
| Observer (side effects) | 2/5 | Review |
| Operation (business steps) | 1/5 | Extract |

**Concern health:**
- Behavioral concerns (shared across models) → good
- Code-slicing concerns (grouping by artifact type) → extract or inline

**God-object indicators:**
- Many methods (50+)
- High churn (frequently modified)
- Mixed responsibilities (persistence + presentation + notifications)

### 4. Current Attributes Audit

Flag all `Current` usage and evaluate by layer:

- **Controllers:** OK (write location)
- **Services:** review (should it pass explicitly?)
- **Models:** violation (extract to parameter)
- **Jobs:** risk (context is absent)

### 5. Service Object Critique

Prevent anemic models:

- Does this service contain logic that belongs in the model?
- Is the service just a thin wrapper around model methods?
- Are there established conventions (base class, naming, interface)?

Identify decomposition opportunities:

- Is `app/services` growing unbounded?
- Do services share patterns that could become abstractions?
- Are there 3+ services doing similar things?

### 6. Anemic Job Detection

Flag job classes that just delegate to model methods:

```python
def notify_recipients_job(*, post_id):
    post = Post.objects.get(pk=post_id)
    notify_recipients(post=post)
# Thin is not automatically anemic: this establishes the persisted-ID boundary.
```

**Signals:**
- Job's `perform` is single line calling method on argument
- Model has `*_later` method that just calls `enqueue(model_id=self.pk)`
- `app/jobs` has many similar thin wrappers

**Recommendation:** Retain a thin explicit worker entrypoint when it owns retry, serialization or execution context:

```python
# Keep task registration explicit in the configured backend.
# Do not generate enqueue methods on domain models to save a wrapper file.
notify_recipients(post=post)
```

### 7. Abstraction Assessment

Evaluate pattern choices:

- Is this the right pattern for the problem?
- Is there a simpler solution?
- Does it follow established conventions?
- Is this premature abstraction?

## Review Checklist

### Layer Violations (Critical)
- [ ] Models don't access Current attributes
- [ ] Services don't accept request/params objects
- [ ] Controllers don't contain business calculations
- [ ] Views don't query database directly (beyond simple associations)
- [ ] Mailers aren't called from model callbacks
- [ ] **Non-AR classes under `<feature>/models/` don't call HTTP/SDK clients, LLM SDKs, task enqueue or mail delivery, or `configured_channel_layer.group_send`** — those belong in `<feature>/operations/` / `<feature>/ai/` / `<feature>/integrations/` (see [analyze-services §3.6.4](analyze-services.md#364-application-shaped-classes-under-appmodels--promote-up))
- [ ] **LLM/AI SDK callers (`the installed LLM SDK`, `OpenAI`, `Anthropic`, …) live in `<feature>/ai/`** — not under `<feature>/models/` as "calculators" (see [analyze-services §3.6.5](analyze-services.md#365-thin-sdk--broadcast-wrappers--delete-hoist-or-promote-in-that-order) + Phase 2.1 cluster table)
- [ ] **No thin SDK / broadcast wrappers** — a class whose only job is to forward to `configured_channel_layer.group_send` / `provider.generate` / etc. without policy is dead weight; check the SDK's docs (the installed LLM SDK ships its own retries, the configured channel adapter's broadcast is already the public API)

### Callback Health (Warning)
- [ ] New callbacks score 4+ on the scale
- [ ] No operation callbacks (business process steps)
- [ ] No callback control flags (`skip_*`, `unless: :flag`)

### Concern Health (Warning)
- [ ] Concerns are behavioral (can be tested in isolation)
- [ ] No code-slicing (grouping by artifact type)
- [ ] Concerns aren't overgrown (50+ lines)

### Service Health (Suggestion)
- [ ] Services follow established conventions
- [ ] Domain logic remains in models (no anemic models)
- [ ] Services aren't just thin wrappers

### Model Health (Suggestion)
- [ ] No god-object indicators (high churn × complexity)
- [ ] Clear separation of concerns
- [ ] Reasonable method count

## Resolving Violations

When identifying a layer violation (e.g., model triggering notification):

### 1. Trace the Call Chain

Find who calls the violating code:
```
Controller/Job → Service → Model (violation here)
```

### 2. Identify Existing Orchestrators

Look for services, forms, or controllers already coordinating this flow. Check:
- `<feature>/operations/` for related services
- `<feature>/forms/` for form objects handling this operation
- Controllers that initiate the action

### 3. Recommend Moving to Orchestrator

If an orchestrator exists, recommend moving the side effect there:

```python
@transaction.atomic
def apply_paid_invoice(*, invoice):
    license = License.objects.select_for_update().get(pk=invoice.license_id)
    license.prolong(until=invoice.coverage_end)
    license.save(update_fields=["expires_at"])
    DeliveryIntent.objects.create(license=license, event="purchased")
```

### 4. No Clear Orchestrator

If no existing orchestrator, list options without being prescriptive:
- Move to controller (if called from a single controller action)
- Create service object (if complex orchestration needed)
- Create form object (if user input involved)

Let the user decide based on their context.

## Reviewing Test Files

When reviewing test files, apply these principles:

### Never Recommend Testing Private Methods via `send`

Private methods are private for a reason — they're implementation details. Never suggest:

```python
# Bad: tests couple directly to private orchestration steps.
processor._parse_json()
processor._import_board()
processor._import_columns()
```

If private methods need isolated testing, that's a signal the class should be decomposed into smaller public objects. Say that instead.

### Expensive Operations: Combine Assertions Over One-Per-Test Dogma

When setup is expensive, use Django TestCase.setUpTestData or correctly scoped pytest fixtures. Preserve isolation: database-mutating tests must not share mutable state across transactions. Multiple assertions can describe one cohesive behavior.

The pragmatic answer: **combine assertions in fewer tests**. This is better than the alternatives (slow suite, or testing privates via `send`):

```python
@pytest.mark.django_db
def test_import_creates_board_and_contents(validated_import):
    result = import_board(source=validated_import)
    assert result.board.name == "HR Manager"
    assert result.board.columns.count() == 3
    assert result.board.columns.filter(name="Inbox").exists()
    assert result.cards_count == 5
    assert result.comments_count > 0
```

Keep separate tests only for genuinely independent scenarios (error paths, edge cases with different fixtures).

### Removing Duplicate Tests: Show What Replaces Them

Never recommend simply deleting tests without showing what takes their place. When a higher-layer test duplicates a lower-layer test (e.g., TrelloImport tests duplicating Processor tests), replace the duplicates with a **delegation test** that verifies the lower layer is invoked correctly:

```python
@pytest.mark.django_db
def test_import_tracks_completion(import_record, provider):
    process_import(import_id=import_record.pk, provider=provider)
    import_record.refresh_from_db()
    assert import_record.status == "completed"
    assert import_record.completed_at is not None
# Mock external provider boundaries, not private processor methods.
```

This proves TrelloImport delegates to Processor without re-testing all of Processor's behavior.

## Output Format

Default review output shape:

```markdown
## Layered Python Review

### Files Reviewed
- path/to/file.py (Presentation|Application|Domain|Infrastructure)

### Layer Analysis
- **Layers touched:** [list]
- **Data flow:** OK | Violation detected

### Findings

🔴 **Critical: [Issue Type]**
Location: `path/to/file.py:line`
` ` `text
# Problematic code
` ` `
**Problem:** ...
**Fix:** ...

⚠️ **Warning: [Issue Type]**
Location: `path/to/file.py:line`
**Problem:** ...
**Recommendation:** ...

💡 **Suggestion: [Issue Type]**
[Description with alternative approach]

### Summary

**Good:** [what's working]
**Needs Attention:** [prioritized list]
**Priority:** [what to address first]
```

If there are no findings, say so explicitly and note any residual risks or missing verification.

## Severity Levels

### 🔴 Critical (must fix)
- Layer violation (reverse dependency)
- Ambient context in models used for business logic
- Request objects in services
- Business logic in controllers doing domain calculations

### ⚠️ Warning (should fix)
- Low-scoring callbacks (1-2/5)
- Code-slicing concerns
- Anemic-model risk
- Missing service conventions

### 💡 Suggestion (consider)
- Extraction opportunity
- Pattern alternative
- Convention improvement
- Test layer mismatch

## Example Review

```markdown
## Layered Python Review

### Files Reviewed
- <feature>/views/orders_controller.py (Presentation)
- <feature>/models/order.py (Domain)
- <feature>/operations/process_order_service.py (Application)

### Layer Analysis
- **Layers touched:** Presentation, Application, Domain
- **Data flow:** Violation detected

### Findings

🔴 **Critical: Layer Violation**
Location: `<feature>/models/order.py:45`
` ` `python
def complete(self):
    self.completed_by = ambient_actor  # Bad: hidden authorization context.
    self.save(update_fields=["completed_by"])
` ` `
**Problem:** Model depends on Current (presentation context). This will fail silently in background jobs.
**Fix:** Accept user as explicit parameter:
` ` `python
def complete(self, *, actor):
    self.completed_by = actor
    self.save(update_fields=["completed_by"])
` ` `

⚠️ **Warning: Operation Callback**
Location: `<feature>/models/order.py:12`
` ` `python
@receiver(post_save, sender=Order)
def sync_after_save(sender, instance, **kwargs):
    transaction.on_commit(partial(sync_to_warehouse, instance.pk))
` ` `
**Problem:** This is a business operation (score 1/5), not a model concern.
**Recommendation:** Move to controller or use event-driven approach with an explicit operation and configured delivery adapter.

💡 **Suggestion: Anemic Model Risk**
Location: `<feature>/operations/calculate_order_total_service.py`
**Problem:** This calculation (`items.sum(&:subtotal) * discount_rate`) is domain logic that belongs in the Order model.
**Recommendation:** Move `#calculate_total` to Order model. Services should orchestrate, not contain domain logic.

### Summary

**Good:**
- Clean controller structure
- Proper use of strong parameters

**Needs Attention:**
1. 🔴 Fix ambient_actor in Order model (will break in background jobs)
2. ⚠️ Move domain logic from service to model
3. ⚠️ Extract warehouse sync callback

**Priority:** Address layer violation first, then refactor service/model boundary.
```

## Related

- [Service-layer audit](analyze-services.md) — authoritative source for service classification (Phase 2.2), misplaced-code checks (§3.6.1–§3.6.5), and the "models-first variant" verdict criteria
- [Specification test](../references/core/specification-test.md)
- [Layer violations](../references/anti-patterns/layer-violations.md)
- [Callbacks anti-patterns](../references/anti-patterns/callbacks.md)
- [Service Objects anti-patterns](../references/anti-patterns/service-objects.md)
- [AI Integration](../references/topics/ai-integration.md) — the `<feature>/ai/` layer destination for LLM-backed classes
- [Current attributes](../references/topics/current-attributes.md)
