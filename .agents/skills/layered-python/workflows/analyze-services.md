---
lint-skip:
  - rule: reference.length
    reason: "Comprehensive multi-phase service-layer audit; the three phases (discovery, clusters, cross-cutting) are sequential and benefit from being read together. Splitting them fragments the methodology."
---

# Service-Layer Audit Workflow

Deep audit of the Application layer (`<feature>/operations/` and service-like classes elsewhere) against Chapter 5 of *Layered Design for Ruby on Rails Applications*.

## Contents

- [Purpose](#purpose)
- [Core Idea](#core-idea)
- [How This Report Justifies Recommendations](#how-this-report-justifies-recommendations)
- [Phase 1 — Discovery](#phase-1--discovery-what-does-this-codebase-have-and-what-does-it-call-a-service)
- [Phase 2 — Clusters](#phase-2--clusters-promote-up-or-demote-down)
- [Phase 3 — Cross-cutting findings](#phase-3--cross-cutting-findings-the-codebase-insights-supply)
- [Reporting Principles](#reporting-principles)
- [Read more](#read-more)
- [Output Format](#output-format)
- [Related](#related)

## Purpose

Answer one question: **is the service layer healthy, and if not, what concrete proposals would shape it?**

This is a focused complement to the architecture-analysis workflow. Where the parent workflow surveys the whole codebase and emits a **brief** service-layer summary (tier, convention strength, top 3 cluster headlines, smell counts), this workflow produces the **full** report — empirical mirror, per-cluster proposal blocks with contracts and test wins, classification rules, cross-cutting findings. Run the architecture-analysis workflow first for the wide view; run this one when the brief surfaces something worth resolving.

## Core Idea

> `<feature>/operations/` is a waiting room for code. Until a corresponding abstraction (train) arrives, code can sit there. But space is limited—don't overcrowd.

Two failure modes are equally bad:

1. **Bag of random objects** — a sprawling `<feature>/operations/` with no shared conventions, where each file is a unique snowflake.
2. **Anemic models** — services that strip business logic out of models, turning the domain layer into a data container.

The healthy state is **specialization**: as patterns emerge in the waiting room, they get promoted to dedicated abstractions (forms, queries, policies, presenters, deliveries, …) with their own conventions and shared abstractions. A small `<feature>/operations/` with rich `app/{forms,queries,policies,deliveries,...}/` is the target.

This command measures how far the codebase is from that state — and proposes, per cluster, the **next abstraction's interface, machinery, and what writing a new instance of it will feel like**.

## How This Report Justifies Recommendations

Design principles alone don't move teams. **Every recommendation in the output must be backed by concrete, observable consequences** — focus on what the *current* shape costs and what the *promoted* (or demoted) shape gives back.

The two engines of justification are:

1. **Tests** — every change to the service layer changes the test layer. The report must describe what spec setup looks like *now*, what shared helpers/matchers/idioms become available *after* the change, and what the **specification test** reveals about each candidate. A spec that describes responsibilities outside its layer's primary concern is itself the proof a refactor is needed.
2. **Concrete current pain** — slow specs, repeated stubs, brittle assertions, layer leakages, duplicate coverage between service and model specs, unclear failure messages. These are observable; the report must point at examples in the codebase, not generic descriptions.

Recommendations stated as bare design principles ("services should be cohesive", "models should be rich") are insufficient and should be rewritten in terms of one or both of the above.

The command is organized into three phases. **Phase 1 — Discovery** answers "what exists and what does this codebase call a service". **Phase 2 — Clusters** turns each detected cluster into a concrete proposal (promote up or demote down). **Phase 3 — Cross-cutting findings** surfaces everything that doesn't belong inside a cluster.

---

## Phase 1 — Discovery: "What does this codebase have, and what does it call a service?"

### 1.1 Waiting-Room Gate

Compute four numbers from the codebase root:

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

**Skip the cluster analysis (Phase 2 and Phase 3.1 — Convention Strength) if `service_count < 10` OR `service_share < 0.10`.** Always run Phase 1.3 (hidden services in `<feature>/models/`) and the Phase 3 sections that scan models regardless.

When the gate fires, the report's verdict line says so explicitly and offers no recommendations for `<feature>/operations/` — only for `<feature>/models/`.

### 1.2 How This Codebase Defines a Service Object — the empirical mirror

**This is the foundation for every later proposal.** Sample 5–10 representative service files internally and synthesize the project's own implicit design pattern. The point is to make the team's *unspoken* convention visible at a glance — and to anchor every per-cluster contract suggestion in Phase 2.3 to what already exists.

Sample broadly: pick the most-recently-modified files, the largest files, and a few short ones. For each, note class shape, call interface, parameter style, return shape, naming, and side-effect surface — internally, as background for the synthesis.

**The output is exactly one sentence — no code, no numbers, no percentages.** It states the *inferred design pattern* in plain prose, the way you'd answer the question "what's a service in this codebase?" to a new contributor over coffee. Save the supporting metric bullets for Phase 3.1 (Convention Strength) — that's where the *deviation* report lives.

**Always give a definition — even if the only honest one is ironic.** A statement like *"not defined"* or *"no convention"* is not a definition; it's a refusal to name what's there. The mirror's job is to name the design pattern that has emerged from the team's actual choices, however weak. For a codebase with zero shared shape, the honest definition is a Service Object as a *random Python callable placed under `<feature>/operations/`* — that's still a definition (the only convention is the folder), and naming it lands the diagnosis in a way "not yet defined" cannot.

Examples of the right register:

> **In this project, a Service Object is:** a callable class wrapping a single domain operation, with a uniform callable contract and side effects expressed as explicit job or mailer calls.

> **In this project, a Service Object is:** a class that adopts the `Callable` mixin to expose a uniform `.call` entry point, with no shared base or machinery — so each service decides its own discipline beyond the entry-point shape.

> **In this project, a Service Object is:** any Python callable placed under `<feature>/operations/` — every file is its own shape.

That last phrasing — *"any Python callable placed under `<feature>/operations/`"* — *is* the (ironic) definition for "bag of random objects" codebases. The folder is the only convention, and naming that as the convention is more useful to the reader than any percentage table.

The mirror feeds Phase 3.1 (the *deviation* report, where the numbers live) and every Phase 2.3 cluster proposal (which builds on or breaks from the existing convention).

### 1.3 Hidden Services in `<feature>/models/`

The Domain layer is allowed to contain service-shaped classes — Chapter 6 of *Layered Design* names this the **domain services** sub-layer. Query objects, calculators, resolvers, and other pure domain operations that don't naturally fit on a single Django model legitimately live under `<feature>/models/`. The rule is **what crosses layer boundaries**, not what shape the class has.

Surface service-like classes in `<feature>/models/` and **classify each as domain or application** using the purpose test (defined in Phase 2.2). The two categories feed different Phase 2 cluster directions:

- **Domain candidates** stay in `<feature>/models/`. They flow into Phase 2 as **demote-down** clusters — the proposal shapes them with a suffix convention and a per-shape shared abstraction, kept inside the Domain layer.
- **Application candidates** are layer leaks. They flow into Phase 2 as **promote-up** clusters — the proposal moves them to `<feature>/operations/` (or the appropriate specialized layer if a cluster is large enough — forms, deliveries, importers, etc.).

#### Detection

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "transaction.atomic|on_commit|def .*task|urllib|requests|httpx|openai|anthropic|send_mail" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

The classification rule (purpose first, regex second) is defined once in Phase 2.2 and applied here.

### Decision gate after Phase 1

- If `<feature>/operations/` is small/absent (the gate fired), the empirical mirror finds no coherent convention because there is nothing to sample, **and** the `<feature>/models/` scan finds no application-layer leaks, **and** no demote-able clusters, **and** no application-shaped classes hiding under `<feature>/models/` (HTTP wrappers, third-party SDK wrappers, LLM-backed agents, multi-step orchestrators that enqueue jobs or call mailers, transport/broadcast wrappers) → emit a short **"Mature decomposition"** or **"Mature decomposition (models-first variant)"** report and stop. (anycable-saaqs and fizzy follow this path.)
- Otherwise → the codebase has a **missing `<feature>/operations/`** (or a missing specialization). Recommend introducing `<feature>/operations/` for the application-layer pieces hidden under `<feature>/models/`, and proceed to Phase 2 to shape the proposal. A single leak or a single application-shaped class is enough to disqualify the "mature decomposition" verdict — the audit's job is to surface it, not to wave it through under a "models-first" banner.

#### Models-first stance recognition

Some codebases keep all logic in `<feature>/models/`, concerns, and jobs by design. Recognize this as a deliberate architectural choice, not a defect, and call out the trade-offs honestly.

**What "models-first" actually means.** *Think on domain objects first, application services second* — **not** "no `<feature>/operations/` at all". A healthy models-first codebase can and should have `<feature>/operations/` for genuinely application-layer pieces: orchestration with downstream side effects (job enqueue, mail, AnyCable broadcast), third-party SDK wrappers, multi-step transactions whose body crosses layers, HTTP clients, transport/broadcast wrappers, AI agent layers. What a models-first codebase lacks is `<feature>/operations/` as the *primary* abstraction or as a *bag of random objects*. When application-shaped classes hide under `<feature>/models/<concept>/`, the recommendation is **introduce `<feature>/operations/`** (and `<feature>/ai/` for LLM clusters) — not "this is fine because we're models-first". The audit must never use "models-first" as a permission slip for keeping cross-layer dependencies in the Domain layer.

**The model-first variant verdict requires a clean `<feature>/models/` scan.** If the scan finds even one application-shaped class under `<feature>/models/` — an HTTP client, an LLM caller, a class enqueueing jobs, a transport wrapper — the verdict is **Mixed**, not "Mature decomposition (models-first variant)". Surface the leak and the missing `<feature>/operations/`; the team's stance is preserved on the parts where it actually holds.

**Signals:**
- `<feature>/operations/` is absent and `<feature>/models/` has deeply nested namespaces (`account/data_transfer/`, `signup/`, `notifier/`, …) holding non-model action classes.
- Behavioral concerns (`Notifiable`, `Eventable`, `Searchable`) carry side-effect callbacks (e.g., `post_save receiver + on_commit :notify_recipients_later`).
- a configured task backend is the substitute for explicit application services (`*Job` files do orchestration that other codebases would put in services).
- A custom `ContextVar` is used liberally for tenancy / user context.

**Verdict:** the architecture-tier line says **"Mature decomposition (models-first variant)"** — same maturity as a codebase with `<feature>/forms/`, `<feature>/queries/`, `<feature>/policies/`, just expressed differently. The waiting room is intentionally absent.

**Risks the team has accepted** (list when the stance is recognized; observable problems that grow with codebase size):

1. **Layer-leak detection is harder.** With no folder boundary, leaks hide in `<feature>/models/<concept>/operation.py` indefinitely. Recommend an explicit lint rule that forbids `request`/`params`/`ambient context` for business decisions in non-model classes under `<feature>/models/`.
2. **Specification test gets blurrier.** Model specs end up testing orchestration behavior. Sample 5–10 model specs and check whether `describe`/`context` blocks describe domain rules vs. side-effect dispatch.
3. **Callback proliferation.** Side effects accumulate as `after_*_commit` callbacks. Run the callback-analysis workflow.
4. **Concerns become a junk drawer.** Watch concerns crossing 100 LOC or with mixed responsibilities.
5. **Job classes attract scope creep.** Run the god-object analysis workflow over `<feature>/tasks/` periodically.
6. **Domain-method overloading on large models** (`User#sign_up_and_invite_team`, `Account#provision_with_default_data`).
7. **`Current` reliance for cross-model context.** Each `ambient context` read is a hidden dependency on execution context.
8. **Observability gaps** — no single place to instrument every business operation.
9. **Onboarding cost** — contributors trained on layered architecture have to unlearn.
10. **Refactoring loss-aversion** — introducing `<feature>/operations/` retroactively is awkward; decide ahead of time when the threshold is crossed.

The recommendations for these codebases are usually **observations to preserve** plus **risks to monitor** — not refactors. The audit's role is to make the trade-offs visible, not to push the team off their stance.

---

## Phase 2 — Clusters: promote up *or* demote down

Goal: for every detected cluster, produce a **proposal** — the layer/abstraction it should become and what that change concretely looks like.

### 2.1 Cluster Detection

Tokenize each service basename and group by trailing/leading verb-noun pattern. A cluster is significant when **≥5 names share the pattern OR the pattern covers ≥10% of services**.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def |dataclass|Protocol" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

**Cluster sources:**
- Suffix/prefix groupings inside `<feature>/operations/` (`*Query`, `*Form`, `*Notifier`, `*Importer`, `*Sync`, …).
- Application-layer candidates surfaced from `<feature>/models/` in Phase 1.3.
- Cross-folder candidates (e.g., service-shaped files in `app/lib/`).

#### 2.1.1 Suffix/prefix clustering is a hypothesis, not a verdict

Naming is a *first-pass grouping signal*, not the answer. Before proposing a shared base for any cluster, **sample-read 3–5 bodies** and check shape homogeneity along the axes that matter for the proposed abstraction: constructor arity, side-effect surface, return value, channel count. If shapes diverge, report the divergence honestly — sub-cluster or split rather than force a uniform base. A cluster of "things named the same" that *do* different things is not a cluster.

#### 2.1.2 Cluster smells — name the diagnosis before naming the fix

Many name-based clusters are not really clusters of "things to consolidate" — they're symptoms of a different problem. Surface these patterns with the right diagnosis so the proposal targets the underlying cause:

**(a) Verb-prefix cluster smell.** When ≥3 cluster members share a verb prefix (`Send*`, `Create*`, `Award*`, `Notify*`, `Process*`, `Generate*`, `Build*`, `Apply*`, `Update*`, `Remove*`, `Sync*`, `Import*`, `Export*`, `Calculate*`, `Compute*`):

- The prefix names an *action*, not a *concept*. Each member is defined as "a thing that does X" rather than "a kind of Y."
- The action almost always belongs to a single service (or shared abstraction) consuming the members; the members themselves should be nouns naming the concepts they represent.
- The fix: rename members to noun-only, often combined with relocation to `<feature>/models/<concept>/`. Do **not** recommend "move the verb to a suffix" — that preserves the confusion. Drop the verb from the per-member name entirely; the verb lives once, in the consuming service or shared abstraction.
- If the cluster contains a member named after the bare verb (e.g., a shared abstraction with the same name as the prefix), that's a strong tell the verb is the cluster's operation and the prefixed members are nouns that should stand alone.
- When this smell fires, also check directory-level naming: if ≥30 top-level files use verb-first naming, surface as a **directory-level finding** ("verb-first filenames scatter related concepts alphabetically — consider namespace grouping by concept").

**(b) Action-axis grouping.** When the cluster takes the form of parallel namespaces each containing single-action classes (`add_x`, `remove_x` repeated per `<X>`):

- **Regroup by bounded concept.** One multi-action service per concept exposing `#add`, `#remove`, etc. The file name says the concept; the method name says the action.
- **Surface the latent-bug risk.** Action-axis copy-paste hides bugs in the shared shape — copy-paste artifacts invisible from the class names alone.
- Do not propose flattening into action-parameterized classes — that's the dedup that misses.

**(c) Folder-level mixing of different responsibilities.** When a folder contains both delivery-shaped classes (notifiers, mailers, messengers) **and** record-management operations (`Remove*`, `Cleanup*`, `Update*`, `Purge*`), flag the **mixing** as a sub-finding. Different responsibilities, identical surface — split first; destination of the operations is a secondary choice.

**(d) Non-class files in `<feature>/operations/`.** During sampling, look at top-level non-class files: `module Foo; def self.x; end; end`-shaped files with no AR/HTTP/job calls and `Hash`-returning methods are **presenters/serializers**. Surface as a dedicated finding ("presenter/serializer living in services/") with the destination layer (`app/serializers/` or `app/decorators/`).

**(e) Thin-wrapper cluster — missing cross-cutting abstraction.** When a cluster of services all follow the pattern `<trivial domain operation> + <same cross-cutting side effect>`, the recommendation should target the **cross-cutting concern** (extract a reusable abstraction for the side effect), not the cluster shape (consolidate N services into 1). The cluster dissolves as a consequence — each service was only a wrapper because the side effect had no reusable home. Name this diagnosis as **"missing cross-cutting abstraction"** rather than "verb-prefix cluster" or "consolidation target."

The tell: each service body is ≤30 LOC, the domain operation is one AR call, and the remaining lines are identical boilerplate for the same side effect (event dispatch, audit logging, webhook delivery, protocol distribution). The services aren't N pieces of application logic — they're N copies of one infrastructure pattern that nobody named.

Distinguish from (a): verb-prefix clusters have members that should be renamed to nouns and consumed by one service. Thin-wrapper clusters have members that should *dissolve entirely* — the abstraction for the side effect absorbs their raison d'être.

**(f) CRUD clusters — distinguish form-object from action candidates.** Within a verb-prefix CRUD cluster, distinguish **form-object candidates** (`Create`, `Update` — accept params, validate, persist) from **action candidates** (`Delete`, `Add`, `Remove`, `Revoke` — accept a domain object, perform a single operation). The two groups may want different destinations:

- Form-object candidates → form objects (`<feature>/forms/`) or `forms.Form` wrappers.
- Action candidates → inline with a cross-cutting concern wrapper, model methods, or thin orchestration services.

Do not propose the same destination for both groups unless their shapes genuinely converge.

**(g) Cross-cutting concepts that span layers.** When a class-method-only file touches both presentation (view modification, content filtering, rendering transformations) **and** domain actions (flagging, blocking, state changes), don't reflexively demote to `<feature>/models/`. It may legitimately span layers — that's what makes it a service (or at least a waiting-room resident). The diagnosis is **"flat placement"** (needs namespacing within `<feature>/operations/`), not **"wrong layer"** (needs relocation to `<feature>/models/`). The test: if the class would need to import from both the domain layer and the presentation layer to do its job, it sits above both — that's the application layer by definition.

| Trailing pattern (case-insensitive) | Wants to be (the layer/abstraction) | Example libraries (any one is fine) | Reference |
|---|---|---|---|
| `Query`, `Finder`, `Search`, `Filter`, `Lookup` | Query / Filter layer | QuerySet methods, explicit query functions, validated filters | `references/patterns/query-objects.md`, `filter-objects.md` |
| `Form`, `Builder`, `Wrapper`, `Input` | Form-object layer | Django Form and ModelForm | `references/patterns/form-objects.md` |
| `Policy`, `Authorizer`, `Permission`, `Access` | Authorization layer | `explicit Django policies`, `Django permissions`, `project policies`, hand-rolled policies | `references/patterns/policy-objects.md` |
| `Presenter`, `Decorator`, `View`, `Renderer` | View / presentation layer | `React components`, `phlex`, `draper`, hand-rolled presenters | `references/patterns/presenters.md` |
| `Notifier`, `Notification`, `Mailer`, `Delivery` | Notification / delivery layer | `an explicit delivery function`, `noticed`, hand-rolled delivery Python objects over ActionMailer + others | `references/topics/notifications.md` |
| `Importer`, `Exporter`, `Sync`, `Webhook`, `Handler`, `Listener` | Background or event entrypoints | The configured task backend; explicit worker functions | `references/anti-patterns/jobs.md` |
| `Manager`, `Coordinator`, `Orchestrator` (no domain word) | Suspect god service — inspect | n/a | god-object analysis workflow |
| `Serializer`, `Marshaller` | API serialization layer | `explicit DTOs`, `panko`, `ams`, `jbuilder` | `references/patterns/serializers.md` |
| `Agent`, `Extractor`, `Suggester`, `Writer`, `Checker`, `Classifier`, `Summarizer` **when the body calls an LLM SDK** | Application operation plus infrastructure provider adapter | Existing provider SDK with explicit schema, timeout and errors | `references/topics/ai-integration.md` |
| `Calculator`, `Score`, `Metric`, `Resolver` | Domain-services sub-layer (calculators, resolvers, queries — **demote candidates**) | hand-rolled Python objects in `<feature>/models/` | `references/patterns/query-objects.md` (Chapter 6 shape) |
| `Builder` (when wrapping a value), small bundles of related attributes with no behavior of their own | Value object (**demote candidate**) | `Data.define`, `composed_of`, `store_model` | `references/patterns/value-objects.md` |
| `Profile`, `Greeter`, `*Information` (a slice of one model's behavior) | Collaborator / delegate object (**demote candidate**) | explicit collaborator or dataclass | `references/patterns/collaborator-objects.md` |

The middle column lists the **abstraction layer** the cluster wants to become. The right column lists **example libraries** — *any one* satisfies the recommendation; the team picks based on existing dependencies and preferences. A cluster's report section mentions the layer first, names 2+ library options, and uses one as a short illustrative example. It does not declare a winner.

### 2.2 Cluster Classification: promote vs. demote

Many "services" should not be services at all. Classify each detected cluster's destination using **purpose first, regex second**.

| Direction | Destination | Trigger |
|---|---|---|
| **Promote up** to a specialization layer | `<feature>/forms/`, `<feature>/queries/`, `<feature>/policies/`, `<feature>/delivery/`, `<feature>/presentation/`, `web/src/components/`, `<feature>/integrations/`, `<feature>/operations/`, `app/importers/`, etc. — or `<feature>/operations/<specialization>/` nested | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |
| **Demote down** to the Domain layer | `<feature>/models/<concept>/<x>_calculator.py`, `<feature>/models/<x>_query.py`, a flat `<feature>/queries/`, `<feature>/domain/`, `<feature>/queries/` | The cluster's body stays in the Domain layer (no mailers/jobs/services/SDK calls; purpose is to *derive information from domain data*) |
| **Demote down** to a value object | A frozen value class under `<feature>/models/` (or a dedicated namespace) | The "service" wraps a small bundle of related attributes with pure transformations — a unit of meaning, not a unit of work. See `references/patterns/value-objects.md`. |
| **Demote down** to a collaborator / delegate object | A small delegate object that lives alongside its primary model (plain Python or a polymorphic AR row) | The "service" extracts a slice of behavior tightly coupled to one model's data (e.g., a contact-information delegate of `User`). See `references/patterns/collaborator-objects.md`. |

#### The classification rule (purpose first, regex second)

For each candidate, read the file and ask: **what is the purpose of this class — does it derive information from domain data, or does it orchestrate a side effect that escapes the Domain layer?** The classification is about *purpose*, not just about which method calls appear in its body.

**Mechanical signals — direct cross-layer calls.** A candidate is clearly **application-layer** if **any** of these appear directly in the body:

- Calls a mailer, job, or another service (`*Mailer\.`, `\.deliver_(now|later)`, `\.perform_(now|later|async|in)`, `\w+Service\.call`).
- Calls a third-party SDK / HTTP client (`Stripe.`, a Slack SDK, boto3, a Twilio SDK, `HTTP\.`, httpx, `urllib.request`, requests, urllib).
- Calls an LLM / AI SDK (`the installed LLM SDK`, `OpenAI.`, `Anthropic.`, a Gemini SDK, a Cohere SDK, a Bedrock SDK, a Replicate SDK, the configured AI framework). Treat as a cross-layer call; the cluster wants the AI agent layer — see the Phase 2.1 cluster table row for `Agent`/`Extractor`/`Suggester`/`Writer`/`Checker`.
- Reads `ambient context` for business decisions, or accepts `request`/`params`.
- Performs file/storage operations (`File.write`, `Tempfile`, a storage adapter).

**Conceptual signal — the purpose test.** A candidate can also be application-layer **even when none of the mechanical signals fire** — when its purpose is to orchestrate a pipeline whose ultimate effect leaves the Domain. The most common example is a notifier:

```python
def notify_recipients(*, recipients, source, actor):
    return Notification.objects.bulk_create([
        Notification(user=recipient, source=source, creator=actor) for recipient in recipients
    ])
```

The body only does `Notification.objects.create(...)` — ORM persistence — and the regex says "domain". But the `Notification` records exist *solely* to trigger emails / push / Slack delivery downstream (typically a job consuming the new records, or an `transaction.on_commit` on `Notification` itself). The notifier's *purpose* is "send a notification when X happens", which is by definition application-level orchestration of side effects. **It is an application service, not a domain service**, regardless of where the file lives.

Apply the purpose test by asking:

1. **Does this class exist to coordinate side effects** (notifications, jobs, deliveries, integrations, state transitions that have outward-facing consequences)? → application.
2. **Does this class exist to derive information from domain data** (calculate a value, find records matching a rule, compute state from associations, transform a value object)? → domain.
3. **Does this class wrap a small bundle of related attributes with pure transformations and no identity of its own?** → value object.
4. **Does this class extract a slice of behavior tightly coupled to one model's data, in a way that needs its own type?** → collaborator / delegate object.

Other cases that pass the regex but are conceptually application-layer:

- Classes that create Django model instances whose lifecycle triggers `transaction.on_commit` jobs / mailers further down — the persistence call is the trigger; the purpose is the trigger.
- Classes that update an attribute that another model's callback responds to (a state-change notifier in disguise).
- Classes that wrap a multi-step domain mutation that, taken together, defines a use case (e.g., `activate_account` setting `activated_at` and `welcome_sent_at` and creating an `AuditEvent` record).

Other cases that pass the regex but are conceptually domain-layer:

- Pure calculators that consume already-loaded domain values. A storage read is infrastructure I/O even when it only reads; keep it explicit and separate from a pure calculation.

**LLM/AI SDK calls are not domain calculators.** Calls to `the installed LLM SDK`, `OpenAI`, `Anthropic`, etc. are network round-trips to a third party — like a remote storage read, infrastructure I/O. A "calculator that derives information from domain data via an LLM" is an **agent**, and the cluster's destination is the AI agent layer (`<feature>/ai/` — see Phase 2.1 cluster table). Do not write "purpose-first carve-out, classification is domain" for an LLM-backed class. Even a single LLM caller is application-layer; ≥3–4 of them form a recognizable cluster worth promoting to a dedicated layer.

**Name signals — corroborating only.** Combine with the mechanical or purpose test:

- `*_calculator`, `*_query`, `*_finder`, `*_resolver`, `*_score`, `*_metric` — typically domain.
- `*_notifier`, `*_sync`, `*_importer`, `*_exporter`, `*_handler`, `*_observer`, `*_creator` (when it triggers downstream effects) — typically application *even if the body looks pure*.
- `*_builder` — depends on what's being built (a value object → value-object demote; an Django model instance + side effects → application).
- `*_dispatcher`, `*_router`, `*_publisher`, `*_emitter` — orchestration vocabulary, almost always application.

**Purpose first, regex second.** A regex match without a purpose match is a false positive (e.g., `MetricsDocument` named `*Api` but composing pure JSON); a purpose match without a regex match is the more dangerous case (e.g., a notifier with only `objects.create()` in its body).

#### Purpose test must account for downstream consumers

When applying the purpose test to a class that creates Django model instances, check whether the record model has callbacks or other consumers that turn record creation into delivery. If creating the record IS the delivery trigger, AR-creating classes are notifiers regardless of how much query logic is in their bodies. The fix for "heavy query logic inside a notifier" is **query extraction** (a separate query object the notifier consumes) — **not demotion to domain**. The notifier's purpose is downstream, even when the body looks pure.

#### Ambient infrastructure calls are not cross-layer side effects

Some codebases have a pervasive infrastructure concern that appears at every layer — federation, tenant resolution, external identity lookup, distributed tracing, multi-tenancy scoping. Don't count calls to that concern as "cross-layer side effects" for classification purposes. **The test:** if removing the call would break the feature's core purpose (not just a nice-to-have), it's **ambient infrastructure**, not an optional side effect.

Name these explicitly as "ambient infrastructure" in the report rather than silently filtering — the reader should see the reasoning. Don't let ambient infrastructure disqualify a class from its natural classification (e.g., a query object that resolves external identities is still a query object).

#### Domain concepts misfiled as services

When a service-cluster member has the shape `def operation(): query records; for each, persist + follow-up`, recognize this as **domain-concept-misfiled-as-service**. The query-and-criteria part describes "what entity X is" or "who qualifies" — that's domain. The persist-loop part is the service operation. Recommendation:

1. **Promote each member to a domain object** under `<feature>/models/<concept>/`. Plain Python class — no models.Model base. Typical three-method contract: a key/slug, a qualifying-entities method (returning a relation), and a per-entity helper.
2. **Inline queries inside the domain object are fine** — they're pure-domain once the file lives in `<feature>/models/`. Don't extract into separate query objects unless reused across ≥2 consumers or complex enough to warrant their own spec.
3. **Collapse the service layer to one file** — one service with the verb, consuming any domain object.

This pattern recurs across notifications (recipient queries), badges (eligibility), scoring/ranking clusters. Name it as: "the cluster is one concept-per-class away from working — but the missing concept is *the noun*, not *an action on the noun*."

#### Eligibility/feasibility checks are system constraints, not model methods

When a service checks eligibility/feasibility rules (`Can*`, `Allowed*`, `Eligible*`, `Permitted*`) that are neither **authorization** (user-may-do-X) nor **validation** (data-is-valid), classify as **system constraint** — a distinct category from "model method candidate." Don't reflexively demote to the model.

- If cluster count <3, note as an emerging abstraction and recommend waiting.
- If ≥3, propose a constraint/rule abstraction with a dedicated suffix and placement.

#### External-vocabulary mappers are infrastructure-adjacent

When a service maps between an external system's vocabulary (third-party categories, transaction codes, admin statuses) and internal display/grouping labels, classify as an **external-vocabulary mapper**. **Don't recommend moving to `<feature>/models/`.** Recommend: drop the runnable interface (`#run` / `#call`), keep co-located with the consuming service/engine, use a class-method or constant-hash shape. The test: if the external system changed its taxonomy, would this class need to change? If yes, it's infrastructure-adjacent.

#### Wrong-abstraction caution

Chapter 5's specialization-cluster threshold (≥5 names or ≥10%) is a **prompt to inspect**, not a mandate to extract. A wrong abstraction is worse than duplication. For each detected cluster apply this guardrail:

- **Tiny cluster (5–7 files) with low structural similarity** → recommend "wait — keep duplication until the shape is unmistakable". Surface the cluster, but do not push promotion. Cite which two files in the cluster look least alike to make the point concrete.
- **Cluster of any size where the candidates differ in dependency depth** (e.g., some take a single Django model, others orchestrate jobs/mailers/external APIs) → splitting may produce a smaller, real cluster plus orphans. Prefer extracting only the cohesive subset.
- **Mature cluster (≥8 files) with uniform shape** → promotion is a clear win.

The bias is against premature extraction. State this explicitly in the cluster section when the count is borderline. Borderline clusters get a short proposal block (steps 1–3 + step 8) and skip steps 4–7.

#### The "domain method" alternative for single-class candidates

The classification rule above applies to **clusters**. A single application-layer candidate may also pass a stricter check that turns it into a *method on the model* rather than a separate class. The rule mirrors the cluster rule but operates at the file level:

- **Take one primary domain object (`models.Model` model) as input. Other inputs are value objects or simple scalars.**
- **Body uses only Domain-layer operations** on that model and its associations: AR persistence, value-object math, state transitions, validations, scope queries.
- **Body does NOT call mailers, jobs, services, HTTP/API clients, `ambient context`, `request`, `params`, file/storage APIs.**
- **The operation is a domain rule, invariant, calculation, or state transition** — not orchestration.

If the candidate is fully clean → recommend moving the body to a method on the model. *"Move `XxxService#call` to `Xxx#verb_form` — body is pure domain."*

If the candidate is *almost* clean (one infrastructure side-effect) → recommend the **layered split**: extract the pure body as a model method, keep the side-effect in a thin orchestrating service that calls the new method then triggers the side-effect. **Do not collapse cross-layer code onto the model** — that turns anemic models into god models.

Layer-bound module-function alternative: if a candidate is stateless, single-public-method, and its body operates within one layer only, recommend the module form (`Module.do_thing`, not `class DoThing; def call`). If the body crosses layers, the service stays a class even when stateless — the class form makes orchestration visible at the call site. These are diagnostic prompts, not violations.

#### Two brakes before recommending demote-to-domain

A demote-to-domain recommendation must clear two checks before being emitted:

**(A) Destination-model god-object brake.** Before proposing to add methods to an Django model, check the destination's god-object signals: LOC, public method count, mixed concerns, callbacks, scopes. If the destination is already heavy (>500 LOC, >40 public methods, >5 mixed concerns, or already on the god-candidate list), **conditionally reject** the demote: the orchestration belongs at the Application layer. Recommend a multi-action service grouped by bounded concept instead. Phrase as: *"this is a legitimate service object — the issue is the cluster's *shape*, not its *layer*."*

When justifying why something is a legitimate Application-layer home, multiple framings are valid (DDD's "operation around a coherent concept," orchestration over multiple collaborators with side-effects, etc.) — pick whichever serves the argument; don't claim any one is canonical.

**(B) Source-complexity brake.** Check the source service's body, not just the destination. Recommend a **collaborator/delegate object** (`ModelCollaborator`) instead of a model method when any of the following is true:

- Body complexity >30 LOC with branching.
- Creates records on models other than the target.
- Calls external services or infrastructure.
- The operation introduces non-core behavior to the model.

When multiple services are always called together from the same call sites in the same order, consolidating into a single collaborator is better than N separate domain methods or N separate collaborator objects — the pipeline is the abstraction, not the individual phases.

### 2.3 The Cluster Proposal Block

For every cluster — promote-up *and* demote-down — the report emits a single block with the following ordered sub-sections. The block is the chassis on which everything else hangs.

#### 1. Cluster identity

Files (count + 2–3 sample paths), the basename pattern that grouped them, and the destination layer (promote / demote / "wait"). One short paragraph.

#### 2. Current pain — observable problems

Sample 2–3 services in the cluster and read their source + spec. Cite specific examples of:

- Repeated stubbing or setup boilerplate across cluster specs (quote a snippet).
- Slow specs that load the controller stack or full DB fixtures where focused tests would suffice.
- Brittle assertions tied to internal implementation rather than behavior.
- Duplicate coverage between the service spec and the underlying model/component spec.
- Layer leakage in tests (`request`/`params` doubles in service specs).
- Inconsistent transaction wrapping across the cluster (e.g., 4/12 wrap, 8/12 don't).

#### 3. Specification-test verdict

Examine test function names, parametrized cases and fixtures. If those contexts describe something **outside** the cluster's true responsibility, the specification test is telling you the wrong responsibility lives in this layer. Quote 1–2 actual test names or case definitions as proof:

- `*Query` service spec asserting SQL/scope shape → that is a query-object spec.
- `*Form` service spec asserting validation messages and error states → that is a form-object spec under Django Form semantics.
- `*Notifier`/`*Sender` service spec stubbing mailer + Slack + webhook → that is a delivery spec with channel matchers.
- `*Detector`/`*Calculator` spec asserting branch coverage on inputs → that is a value-object/method-object spec.
- `*Sync`/`*Webhook`/`*Handler` spec setting `perform_enqueued_jobs` and asserting side effects → that is a job spec.

#### 4. Suggested interface / contract

State the abstraction's shape **as a small Python code block** — use type annotations, keyword-only parameters and dataclasses; use a Protocol only for actual interchangeable implementations. The reader should be able to read it in seconds and know exactly what subclasses look like, what methods exist, what they return, and how peer code calls in.

**Format rules:**
- Show the shared abstraction with its declarative DSL (parameters, hooks) and abstract method placeholders (`def import_row(row); end`).
- Show one concrete function or object from the codebase; require inheritance only when actual substitutability needs it.
- Show the return-value type as a Python dataclass declaration (a dataclass, TypedDict, or a built-in return annotation).
- Show one or two **peer-use call sites** at the bottom (controller, job, management command) so cross-boundary interaction is visible.

**Codebase-faithfulness rule.** Preserve the project’s existing explicit callable, dataclass and exception contracts. Prefer ordinary functions over inherited DSLs; describe changes to an established contract with a migration path.

A contract written in a foreign vocabulary asks the team to adopt a new dependency *before* applying the proposal — that's a hidden second migration the audit didn't recommend. The contract should read as "if we extracted today, this is the shape" — using the project's current building blocks.

Examples:
- Codebase uses keyword-only functions → keep functions; do not add service inheritance to match the source book.
- Codebase has an existing validated input dataclass → preserve it and document any needed contract migration.
- Codebase hand-rolls a Result dataclass → contract uses `Result`, not an uninstalled monadic result.

The exception: when the codebase's own convention is itself the diagnosis (e.g., 6 ad-hoc shared abstractions, no shared shape), the contract proposes the *consolidating* shape and names what's being collapsed. That's not silently substituting; that's the recommendation.

The contract is the abstraction. **Do not name `#call` reflexively** — many specializations want richer verbs:

- **Query layer** → `QuerySet return contract` returning `QuerySet`; chainable.
- **Policy layer** → predicate functions such as can_view and can_update, one per rule.
- **Form-object layer** → explicit save/update operations, plus Django `is_valid()` / `errors`.
- **Delivery / notifier layer** → explicit send or enqueue functions per channel.
- **Importer layer** → `#import` returning a typed result with `count`, `errors`, `imported_records`.
- **Calculator (domain)** → `#value`, `#score`, or a domain-specific verb (`#total`, `#availability`).
- **Collaborator / delegate object** → a focused subset of the parent model's API; the parent uses an explicit method call on its collaborator.

Use a named function for a single operation. A callable object is useful when it carries explicit dependencies; a universal .call convention is not mandatory in Python.

**Example format** (illustrative — for an importer cluster):

````markdown
```python
@dataclass(frozen=True)
class ImportResult:
    imported_count: int
    records: tuple[Scholarship, ...]


@transaction.atomic
def import_scholarships(*, rows, tenant):
    # rows have passed the importer boundary schema; money is never parsed with float.
    records = tuple(Scholarship.objects.create(tenant=tenant, name=row.name, amount_cents=row.amount_cents)
                    for row in rows)
    record_import_audit(tenant=tenant, imported_count=len(records))
    return ImportResult(len(records), records)

result = import_scholarships(rows=validated_rows, tenant=tenant)
```
````

Prefer code (or pseudo-code) snippets over prose tables for the contract. Tables describe; code declares. The reader takes the code as the contract.

#### 5. Optional library hint

*Library options:* list 2+, mark one as the illustrative example. Surface the sketch-on-request offer in **Next Steps**, not inline. The team picks the implementation; the command picks the layer.

#### 6. Shared machinery the shared abstraction hoists

Survey 3–5 cluster files and identify common patterns the shared abstraction can factor out.

| Common pattern across candidates | Goes into the shared abstraction |
|---|---|
| Repeated `transaction.atomic()` blocks | `transaction` delegate; or wrap the entry method in a transaction option |
| Repeated `logging.getLogger(__name__).info("[X] ...")` instrumentation | A logger helper, or `instrument` block via `structured logging / configured tracing` |
| Repeated `raise SomeError, msg` patterns | A `fail_with!(message)` helper that raises a uniform error type |
| Common parameter shapes (e.g., everyone takes a `current_user` and a record) | Required keyword-only actor and record inputs |
| Repeated success/failure return shape | A `Result`/monad return convention |
| Repeated `connection.cursor()` for raw SQL | A SQL-execution helper |
| Repeated `transaction.atomic()` plus `transaction.on_commit()` for callbacks | An `transaction.on_commit` helper (without hidden callbacks) |
| Repeated CSV / file-read parsing in importers | A `parse(io)` helper; per-row error capture; result collection |

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "transaction.atomic|on_commit|def .*task|urllib|requests|httpx|openai|anthropic|send_mail" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

If sampling reveals **no** common machinery worth hoisting, **don't recommend a shared abstraction for its own sake**. The layer can use Python objects that follow a naming convention only — but say so explicitly: *"Each candidate is a unique procedure; the win is namespace/suffix consistency, not shared machinery."*

#### 7. Benefits showcase

The proposal payoff. Five named sub-sections; include all five for promote-up clusters with ≥6 files. Borderline (5–7 files, low similarity) and demote-down clusters include a-c-e and skip d ("Adding a new feature" walkthrough).

**a. Deduplication.** Concrete LOC count saved by the shared abstraction hoisting common machinery; reference 2–3 files where the duplicated pattern currently lives. Example: *"the proposed `transactional` declaration removes 9 explicit `transaction.atomic()` blocks across the cluster — about 18 LOC."*

**b. Common issues solved.** Name 1–2 problems the abstraction prevents — e.g., *"transactional wrapping is currently inconsistent across the cluster (4/12 files wrap, 8/12 don't); the shared abstraction makes this uniform"* or *"error types vary by file (3 distinct `*Error` classes); the base's documented exception contract standardizes the type at the controller boundary."*

**c. Test simplification.** The framework matchers / shared *contexts* / custom-assertion vocabulary unlocked by promotion, with a citation to one current spec each idiom would replace. State the specification-test clarity after promotion as a single-responsibility sentence.

| Layer | Test idioms | Replaces |
|---|---|---|
| Forms | form.is_valid(), form.errors, cross-field cases | Repeated parsing logic |
| Queries | Scoped rows and assertNumQueries where relevant | HTTP setup for query behavior |
| Policies | Parametrized actor/record/permission matrix | Scattered ownership checks |
| Delivery | Mock configured provider boundary, assert payload and errors | Live network dependencies |
| Workers | Actual backend enqueue contract plus task unit tests | Guessed queue APIs |
| Importers | Typed input/output and transaction tests | Repeated fixture setup |
| React presentation | Testing Library and Storybook play assertions | String-based HTML comparisons |
| JSON | Explicit sensitive-field allowlists | Model-wide snapshots |
| Domain calculations | Pure inputs and exact values | Transport-layer test setup |

Only introduce shared pytest fixtures when their setup is genuinely shared.
No service base class or third-party matcher is necessary for these assertions.

**d. "Adding a new feature" walkthrough** *(promote-up clusters with ≥6 files only — borderline and demote-down clusters skip this sub-section)*

Show what creating the next instance of this abstraction looks like — before/after — to demonstrate the pull, not just the diagnosis. Tie it to a concrete hypothetical drawn from the codebase (e.g., "imagine adding a `RecentSignupsQuery` to the cluster" or "imagine adding the next CSV importer for a third-party export").

```markdown
**Today** — adding the next `*Query` to the cluster:

```python
def recent_signups(users, *, since):
    return users.filter(date_joined__gt=since).order_by("-date_joined", "pk")
```

```python
@pytest.mark.django_db
def test_recent_signups_excludes_older_users(old_user, recent_user):
    assert list(recent_signups(User.objects.all(), since=yesterday)) == [recent_user]
```

35 LOC for the file + spec; the author re-derived parameter passing, scope chaining,
and result assertion patterns from a sibling file.

**After promotion** — same cluster, with `query function`:

```python
class UserQuerySet(models.QuerySet):
    def recent_signups(self, *, since):
        return self.filter(date_joined__gt=since).order_by("-date_joined", "pk")
```

```python
@pytest.mark.django_db
def test_query_keeps_the_authorized_scope(account, other_account_user):
    result = account.users.recent_signups(since=yesterday)
    assert not result.filter(pk=other_account_user.pk).exists()
```

~6 LOC of declared contract; the matcher comes from `query function`'s shared base;
the parameter shape is uniform with the rest of the cluster.
```

The walkthrough is what makes the proposal land. Keep each side under ~10 lines of code; tie to the codebase's actual data; show one test (not a suite). Skip the walkthrough when the cluster is too small to accumulate new instances meaningfully.

**e. Cross-boundary conventions unlocked.** Name resolution (e.g., an explicit policy call at the entrypoint); uniform error type at the controller boundary; uniform stub vocabulary in caller specs; framework assertion availability. Example: views catch a documented operation exception while unexpected errors retain their traceback.

#### 8. Placement options

For every cluster, mention **both** placement options. The team decides; the command does not push.

- **Nest under `<feature>/operations/<specialization>/`** (e.g., `<feature>/operations/queries/`) — minimal change, no autoload edits, scopes naming inside the existing folder.
- **Promote to a top-level folder** (e.g., `<feature>/queries/`) — signals first-class abstraction. Right when the abstraction is **common, recognizable, framework-blessed** (`<feature>/policies/` is the canonical example; `<feature>/forms/`, `<feature>/presentation/`, `<feature>/queries/` are well-precedented).

For demote-down destinations:
- **Per-model namespace** (`<feature>/models/<model>/<thing>_calculator.py`) — minimal change, scoped to the parent.
- **Dedicated top-level folder** (`<feature>/domain/`, `<feature>/queries/`) — signals first-class abstraction at the Domain level.
- **Inside the parent model** (for value objects and collaborators) — the parent owns the type via `composed_of`, explicit delegation, or a nested constant.

**Audience as sub-namespace, not peer namespace.** When unifying two clusters that differ only by audience (e.g., user-facing vs. staff-facing), recommend the audience as a **sub-namespace** under one parent, not as a peer folder. The unmarked default is the larger audience; the marked sub-namespace is the smaller. Phrase as "one abstraction, audience encoded in the path."

**Value-object placement: cohesion over relocation.** When proposing placement for a value object, count consumers:

- **0 or 1 consumer → cohesion** (keep next to the consumer, with a conventional filename like `payload.py` / `input.py` / `result.py`).
- **≥2 consumers → hoist** to `<feature>/models/<concept>/` or `app/values/`.

The team gets to choose. The command does **not** push everyone toward `app/<specialization>/`.

### 2.4 Special-case proposal rules

Cluster-level rules that override the default proposal shape when their preconditions fire.

#### Operation-contract vs. event-broadcast side-effects

When proposing notifier extraction for multi-channel side-effects, ask: **could a downstream consumer reasonably opt out of this side-effect?**

- **Yes** → event-broadcast — extract as a notifier.
- **No** → the side-effect is required for the operation to fulfill its contract — it stays inline in the service.

Don't extract a notifier just because a side-effect is multi-channel; extract only when consumers can decline.

#### API-client wrappers — no cross-vendor abstraction without polymorphic usage

Before proposing a cross-vendor abstraction for API-wrapping services, inspect the calling side: do callers use the vendors interchangeably or polymorphically? If each vendor's operations are called from different layers with vendor-specific parameters and different return shapes, they share a *folder* but not an *interface*. Limit recommendations to per-vendor internal cleanup.

Reserve `<feature>/integrations/` for services that are **pure HTTP/SDK wrappers** with no business-logic coupling. When API calls are tightly coupled with the calling context, the API interaction is an implementation detail, not a separable layer.

#### Minimal shared abstraction for small heterogeneous clusters

When a cluster of 3–5 services shares one cross-cutting concern (tracing, logging, error handling) but diverges structurally in the core logic, recommend a **minimal shared abstraction** that hoists only the shared concern — not a full abstraction with abstract methods and a uniform contract. Name this as "minimal base" to distinguish from "full promotion."

Full promotion is justified when the convention-strength uniformity test passes (shared instance state, symmetric coverage, homogeneous implementations — see Phase 3.1). When it doesn't, a minimal base preserves pragmatism without foreclosing future promotion.

#### God-object triage — size vs. coupling vs. placement

Not every large file is a decomposition target. When a god-service candidate is detected, triage along three axes before proposing action:

- **Shape uniformity.** If every method has the same shape (build params → create record, or dispatch → notify), the size is repetition, not complexity. Repetition-driven god objects are **acceptable** — keeping all instances in one place has grepability and audit-surface value.
- **Coupling surface.** Count call sites and classify as imperative (direct `Collaborator(user).verb(...)` calls scattered across layers) vs. event-driven (subscribers, callbacks). Imperative coupling is the real cost — you can't drop or disable the feature without touching N files. Report the number and distribution.
- **Placement.** A god object that is a peripheral concern (auditing, activity logging) should not mix with business-logic services in the flat `<feature>/operations/` listing. Recommend namespace relocation, not decomposition.

The recommendation matrix:

| Shape | Coupling | Action |
|---|---|---|
| Uniform (repetition) | Any | Acceptable god object — flag placement and coupling, not size |
| Mixed (multiple responsibilities) | Low fan-in | Split for readability — extract into modules/classes under a namespace |
| Mixed | High fan-in | Split for readability + audit public API surface (actual entry points vs. nominal public methods) |

**Dispatch god objects** (all-in-one notifications, events, webhooks, alerts) get a specific recommendation shape:

1. **Readability decomposition** — extract conceptually cohesive parts (eligibility resolution, dispatch, channel routing) into modules/classes under a namespace.
2. **Public API audit** — check where `private` starts vs. how many methods are actual entry points (called from outside the class). A class with 20 public methods but only 3–4 real entry points has a misleading API surface — flag this explicitly.
3. **Not a rewrite** — don't propose migrating to a different abstraction or notification framework. The decomposition is structural (namespace + modules), not architectural.

---

## Phase 3 — Cross-cutting findings (the "Codebase Insights" supply)

Goal: surface everything that doesn't belong inside a cluster proposal. The output of this phase becomes the report's `## Codebase Insights` section. Each Phase 3 sub-section *also* feeds evidence *into* Phase 2's cluster blocks (a layer-hygiene leak in a `*Sync` file becomes part of that cluster's "current pain"; a naming-smell candidate becomes part of the corresponding cluster's "demote down" classification).

### 3.1 Convention Strength — the deviation report

The empirical mirror in Phase 1.2 is the *positive* statement of the project's convention. This section is the *deviation* report — where the convention breaks down.

The **single most diagnostic property** of a service layer. Without conventions, the count doesn't matter — the codebase has a "bag of random objects" regardless of size.

Sample 30–60 service files (or all of them when small). For each axis, classify and compute the dominant percentage.

| Axis | What to look for | Strong (≥80%) | Mixed | Weak (<50%) |
|---|---|---|---|---|
| Shared contract | Explicit inputs, returns and exceptions | Consistent within a responsibility | Competing incompatible contracts | Contract unclear; absence of inheritance alone is healthy |
| Call interface | Method named `call`, `perform`, `run`, `process`, `execute` | One verb dominates | Mixed | No discoverable contract |
| Parameter style | Required keyword-only inputs, dataclasses where cohesive | One consistent contract | Competing conventions | Inputs or dependencies hidden |
| Naming suffix | `*Service` suffix vs. no suffix — **the codebase must pick one** | One shape (≥90%) | One shape 70–90% | <70% (mixed) |
| Naming form | Verb-first (`CreateUser`), noun-first (`UserCreator`), or other | One form (≥70%) | Two | Random |
| Return value | Plain values, `Result`/`Success`/`Failure`, a monadic framework, exceptions only | One approach (≥70%) | Two | Caller can't predict |

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "transaction.atomic|on_commit|def .*task|urllib|requests|httpx|openai|anthropic|send_mail" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

#### Naming suffix consistency — flag the deviating minority

The `*Service` suffix is binary: **a healthy codebase picks one rule and applies it to every file**. Either every service is named `CreateUserService` (suffix style) or every service is named `CreateUser` (folder-as-convention style). What you don't want is **both styles in the same directory** — that's an unspoken inconsistency readers have to learn case-by-case.

Apply this rule strictly:

| Suffix-style share | Verdict | Action |
|---|---|---|
| ≥95% | Strong (suffix convention) | None |
| ≤5% | Strong (no-suffix convention) | None |
| 5–95% | **Inconsistent** — flag explicitly | List the files in the **minority** style; the team must rename them to match the majority |

Always show the minority list when in the inconsistent band — that's the actionable bit. Don't summarize as "Mixed naming" without naming the offenders.

The suffix choice itself is also a maturity signal. Codebases with mature decomposition tend to *drop* the suffix (`LicenseForm`, not `LicenseFormService`) because folder location is the convention. If the audit finds `*Service` everywhere *and* zero promoted specializations (`<feature>/forms/` etc. are missing), services and forms/queries/policies haven't yet differentiated — note that in the report.

#### Testing impact of conventions

Convention strength is testing infrastructure in disguise. Translate each axis into observable test consequences in the report:

- **Shared contract.** pytest fixtures and Django TestCase helpers do not require service inheritance. Quote repeated test setup before recommending a fixture or helper; absence of a base class is not a defect.
- **Call interface.** When everyone uses `.call`, callers can be stubbed uniformly (`monkeypatch.setattr(module, "operation", fake)`). When `.perform`/`.run`/`.process` are mixed, every test must remember the right verb. Cite the deviating files.
- **Naming.** Verb-first naming (`CreateUser`) makes the spec read as a sentence. Suffix or noun-first naming (`UserCreator`, `CreateUserService`) requires the reader to translate into actions.
- **Parameter style.** A consistent style (`keyword-only parameters`, kwargs, etc.) lets specs reuse a single factory pattern.
- **Return value.** When return shape is uniform, assertions are uniform.

In the report's Conventions section, **for any axis that scores below the Strong threshold, name a concrete test consequence with a file/line citation**, not just the percentage.

#### Healthy uniformity vs. false uniformity

When analyzing the call-interface axis, distinguish:

- **Healthy uniformity** — a single verb across truly homogeneous services where callers treat them polymorphically.
- **False uniformity** — a single verb across heterogeneous services where sub-namespaces or folder names carry more meaning than the method name.

When false uniformity is detected, **don't automatically recommend consolidation into multi-action objects**. First verify all three:

1. Do the operations share instance state?
2. Is coverage symmetric?
3. Are implementations homogeneous enough to benefit from a shared base?

If all three are "no," it's a naming/interface problem, not structural — recommend per-cluster entry-point naming (below) rather than collapsing to a single class.

#### Per-cluster entry-point naming, not universal `.call`

Each cluster's contract proposal should include an entry-point name suited to its purpose, even when departing from the project's empirical default. The convention-strength score is one input; the cluster's purpose is another.

| Cluster purpose | Suggested entry point |
|---|---|
| Notifier / delivery | send_notification / enqueue_notification |
| Form | `.submit` / `.save` |
| Query | `.resolve` / direct relation methods |
| Policy | predicate functions (`can_access`) |
| Operation | `.call` / `.run` / `.perform` |

Recommending `.deliver` for the notifier cluster does not contradict a "Strong on `.call`" finding for the rest of services — it's the cluster asserting its specialization.

### 3.2 Organization Shape

Walk `<feature>/operations/` once:

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Compute:
- top-level files vs files in subdirs (ratio)
- mean and max namespace depth
- the largest sub-namespaces by file count

#### Flags

| Flag | Trigger | Meaning |
|---|---|---|
| Flat sprawl | >30 top-level files OR >50% of services at the top level | Group under sub-namespaces |
| Mega-namespace | Any subdirectory holding ≥15% of all services | Likely a hidden bounded context worth promoting |
| Generic-named subdir smell | `utils/`, `helpers/`, `lib/`, `misc/`, `common/`, `shared/` with mixed contents | Bag-of-random-objects sub-symptom |

#### Subdir naming nuance

| Pattern | Verdict | Example |
|---|---|---|
| Domain-named | Healthy at any depth | `<feature>/operations/billing/`, `<feature>/operations/onboarding/users/` |
| Specialization-named | Healthy when contents match the name | `<feature>/operations/processors/`, `<feature>/operations/queries/`, `<feature>/operations/deploy_services/` |
| Generic-named with mixed contents | Smell | `<feature>/operations/utils/` containing unrelated logic |
| **Vendor-named top-level folder** | Smell — names infrastructure, not a concept | `app/temporal/`, `app/sidekiq/`, `app/redis/` |
| Vendor-named *sub*-folder under a concept-named parent | Healthy | `<feature>/integrations/stripe/`, `app/workflows/temporal/<workflow>` |
| **Pattern-named with ambiguous fit** | Surface, do not rename | `app/facades/` whose contents could equally be presenters / page objects / aggregators; `app/managers/`, `app/handlers/` when the name covers multiple plausible roles |

#### Vendor-named top-level folders — explicit rule

A subdirectory of `app/` (or of `<feature>/operations/`) named after an infrastructure vendor or library, rather than a concept, hides the architectural role behind a brand name. Examples to flag and how to fix:

- `app/temporal/` → rename to `app/workflows/` and introduce `ApplicationWorkflow`. Temporal.io becomes an implementation detail of the shared abstraction, not the folder name.
- `app/sidekiq/` → rename to `<feature>/tasks/` or `<feature>/tasks/` per the codebase's existing convention.
- `<feature>/operations/aws_client/`, `<feature>/operations/redis/` → fold into `<feature>/integrations/<vendor>/` (where `<feature>/integrations/` is the role) or rename to a domain concept.

**The rule: a top-level `app/<x>/` folder names a layer or a concept, never a vendor.** Vendor-specific implementations live one level deeper, under a concept-named parent. Organization reflects what the code *is*, not what tool it talks to.

A **specialization sub-namespace under `<feature>/operations/` is a perfectly fine alternative** to a top-level `app/<specialization>/` folder.

#### Mis-classified abstractions — diagnose the missing contract, do not pick the new name

When a folder or cluster looks "wrong" because its name does not match its contents, the temptation is to recommend a rename to the pattern that fits best. Resist when the evidence supports more than one plausible classification — a confident rename pretends a debate that the codebase has not had.

**The test before recommending a rename:**

1. **Is the new name unambiguously the right pattern?** *(single canonical name, no plausible alternatives that fit the same evidence)*
2. **Does the rename bring concrete affordances** that "name the role + introduce a shared abstraction" would not? Examples of real affordances: a framework convention triggers behavior (`<feature>/policies/` activates ActionPolicy resolution; `web/src/components/` triggers React component autoload), a library binds to the new shape, a shared abstraction already exists under the new name.

If both answers are yes → recommend the rename. If either is no → the actionable diagnosis is **the missing contract**, which is true regardless of which name wins. Recommend introducing a shared abstraction and a documented role, surface the candidate names as options, and let the team pick the vocabulary.

Examples this rule applies to:

- **`app/facades/` whose contents return view-shaped data with `to_partial_path` markers** could equally be called presenters, page objects, view models, or facades-that-aggregate. The actionable diagnosis is "no `ApplicationFacade` base, no shared interface across the 5 subdirs" — that holds whether the team renames the folder or not.
- **A cluster of `*Resolver` / `*Finder` / `*Loader` / `*Lookup` files that all return `QuerySet`** could become `<feature>/queries/` or stay as `*_resolver.py` with a base — both reasonable. Recommend the contract (`query function returning QuerySet`); list the suffix options; let the team commit to one.
- **`app/managers/` or `app/handlers/`** when the contents span coordinators, event observers, and orchestrators — the umbrella name is too vague for a single rename. The fix is a base + suffix split, not a folder rename.

The error to avoid: surveying *one* axis of the contents (e.g., "they return view-shaped data, so they're presenters") and declaring the rename. A single inspection axis rarely distinguishes between two patterns that legitimately overlap. **Multiple plausible classifications → name the diagnosis, not the verdict.**

A rename recommendation is strong when the canonical pattern is unambiguous (`app/temporal/` → `app/workflows/` is unambiguous because no other layer claims Temporal.io); it is weak when two or more patterns from the canonical vocabulary fit the same evidence.

### 3.3 Naming Smells & Alternative Forms

This section asks a question the structural cluster analysis doesn't: **should this individual service exist at all?** Three mechanical checks plus the layer-bound suggestions for refactoring it away (already covered in Phase 2.2's "domain method" alternative).

#### 3.3.1 `-er` suffix

Class names ending in `-er` (`Manager`, `Processor`, `Creator`, `Sender`, `Exchanger`, `Transferrer`, `Getter`, `Fetcher`, `Updater`, `Mover`, `Cleaner`, `Resolver`) often signal a *procedure-carrier* rather than a real abstraction — the class exists only to hold a verb.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def |dataclass|Protocol" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Caveat: some `-er` suffixes name legitimate framework-blessed roles — `Notifier`, `Validator`, `Serializer`, `Presenter`, `Decorator`, `Renderer`, `Formatter`, `Builder` (when it builds a real object), `Controller` itself. Treat those as healthy; flag only the procedure-carrier flavors above.

Output the suspect `-er` classes as a list, then run §3.3.2 and §3.3.3 against them.

#### 3.3.2 Tautological method/class pair

When the class name's verb-form root and the action method name say the same thing (`IpnProcessor#process_ipn`, `ReportGenerator#generate_report`, `OrderManager#manage_order`, `EmailSender#send_email`, `LinkBuilder#build_link`), the class adds nothing the method couldn't on its own.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "transaction.atomic|on_commit|def .*task|urllib|requests|httpx|openai|anthropic|send_mail" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Implementation: for each detected suspect class `<X><Suffix>`, check if there is a `def <verb>_<x_lowercase>`, `def <verb><X>` or `def <verb>` where `<verb>` matches the suffix root. If yes, flag.

#### 3.3.3 Ubiquitous-language test

A domain service should use terminology from the business glossary. Heuristic: extract the head noun of the class name (drop verb prefixes and trailing role-words like `Service`/`Form`/`Query`) and check whether it appears in `<feature>/models/`, `feature migrations and models`, or `locale/`. If absent, the class names an invented concept.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def |dataclass|Protocol" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Findings here are weak signals on their own; combine with the `-er` smell or tautology smell to identify candidates worth refactoring.

#### 3.3.4 Scheduling-frequency names — inline into jobs

Classes named after temporal scheduling (`Nightly`, `Hourly`, `Weekly`, `Daily`) with 1:1 anemic job peers are a **scheduling-layer duplication** smell.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def |dataclass|Protocol" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Recommendation:

1. **Inline into the job.** Jobs inherently carry scheduling semantics — naming a job `NightlyJob` is fine; naming a service `Nightly` is not. Eliminate the service-as-scheduling-wrapper indirection.
2. **Decompose by category.** Pipeline orchestrators → orchestrator jobs. Batch state transitions → BatchJob → SingleJob → model-method pattern. Ad-hoc fixups → standalone jobs. Multi-responsibility classes must be split before inlining.

Surface as a cross-cutting finding (a single recommendation across the cluster), not per-cluster.

These are **suggestions**, not violations. Teams that committed to `.call` everywhere are making a defensible convention-strength tradeoff (uniform stubbing, uniform interface). The command names the candidates and lets the team choose. Demote candidates surfaced here flow into Phase 2.2's classification table.

### 3.4 Implicit-Workflow Detection

When service A calls services B, C, D from inside its `call`, the workflow has no explicit owner — business logic forms invisible paths through services that share data implicitly.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def |dataclass|Protocol" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

Build a rough call graph (caller file → callee class). Findings to surface:

- **Chains of length ≥3** (A → B → C). State the chain explicitly. Recommend: introduce a named orchestrator that owns the workflow — typically a form (`forms.Form`), an operation (`operation function`), or a saga-like service that names what is happening (`AcceptInvitation`, not the chain `EmailSender → InvitationCreator → MembershipUpdater`).
- **Hub services** with high fan-in or fan-out (called by ≥5 services, or calling ≥5 services). High fan-in suggests a missing domain abstraction; high fan-out suggests an undeclared workflow.
- **Cycles** between services (rare but worth flagging). Always a layer-architecture problem.

Hub services are findings only — high fan-in is data, not a TODO. Inspect for missing domain abstractions before acting.

Workflow-level test win: a named orchestrator's spec describes the workflow steps (one responsibility); the previously implicit chain becomes an explicit, testable narrative.

### 3.5 Layer-Hygiene Violations

Targeted greps in `<feature>/operations/`. Report only sections with findings.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "ContextVar|threading.local|request\.|HttpRequest|render\(|redirect\(" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

For ambient context, classify each usage:

- **Acceptable:** bounded observability metadata, restored with ContextVar.reset(token) in finally; scoped Django locale/time-zone overrides.
- **Concerning:** actor, tenant, audit-owner, authorization or query scoping taken from globals. Pass these explicitly after boundary authorization. Python default arguments are evaluated at definition time; never read a request actor in a function default.

#### Authorization ownership

Authenticate and parse at HTTP or worker entrypoints. Reusable operations may enforce
an explicit actor policy when multiple entrypoints call them. Domain models must not
read HttpRequest or ambient identity. Report inconsistent or missing enforcement;
do not classify an explicit operation-level policy as a leak merely because it is
outside a view. Frontend can props never replace this check.

#### Sinkhole detection

A service that just delegates to a single model method adds no value — the book calls this an "architecture sinkhole".

Heuristic: file ≤20 LOC AND the action method has ≤3 statements AND every statement targets the same single model. Surface 3–5 examples; don't list every case.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

### 3.6 Misplaced Code — not-a-service files

Phase 3 should include a "misplaced code" scan for files in `<feature>/operations/` that **aren't really services**:

- Entirely `class << self` / Singleton with no instance lifecycle.
- Inherit from non-service parents (dependency classes, framework sanitizers).
- Contain no side effects or external calls — just transformations.
- Are self-contained feature modules (parsers + engines + formatters).

Surface as a dedicated finding with per-file destination recommendations (e.g., `lib/`, `app/lib/`, `<feature>/presentation/`).

**However, apply the self-separation gate before recommending relocation.** Many "not-a-service" files are harmless where they are.

#### 3.6.1 Self-separation gate — observation, not recommendation

When a cluster (or individual file) inside `<feature>/operations/` (a) does not inherit the project's service shared abstraction, (b) has its own shared abstraction with a distinct contract, and (c) is well-namespaced alongside its consumers — **do not recommend relocation**. The cluster has already self-separated; the `<feature>/operations/` prefix is cosmetic.

Only recommend relocation when there's a **concrete practical cost**:

- Wrong-layer inheritance pulling in unwanted machinery (middleware, tracing, result ceremony).
- Test-setup overhead from the service shared abstraction.
- Dependency-direction risk that wouldn't exist if the code lived elsewhere.

"It's not technically a service" is an observation worth surfacing — but an **observation**, not a **recommendation**. This applies equally to non-service clusters (storage adapters, payload builders, validators, factories) and to individual non-service files (value objects, error classes, concerns, utilities) co-located with their consumers.

**The litmus test:** can you name a bug, a performance problem, or a developer mistake that this relocation would prevent? If the answer is only "it would be more correct," downgrade to observation.

#### 3.6.2 Mixed-layer files — decomposition, not single relocation

When a file mixes infrastructure machinery (raw SQL helpers, index management, caching primitives, protocol-level operations) with model-specific logic (per-model methods, model-type checks, domain-aware transformations), don't recommend relocating the whole file to one destination. Recommend **decomposition**: infrastructure part to `app/lib/`, model-specific parts to `<feature>/models/<model>/`. Name this as a **mixed-layer file** — a distinct diagnosis from "misfiled service."

The tell: the file contains both generic utility methods that could serve any model AND methods that reference specific model classes by name or use type checks (`Post === object`, `.update_tags_index`).

#### 3.6.3 Console/CLI utilities — specific destination, specific diagnosis

When a service requires interactive I/O libraries (`highline`, `io/console`), takes `IO`/`STDOUT` as a constructor argument, or outputs directly to stdout, flag as a **command handler** (not just "not a service"). Recommend `lib/tasks/` as the destination — not generic `lib/`. The distinction matters: `lib/tasks/` signals "this is tooling invoked from the command line," which is a precise diagnosis.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

#### 3.6.4 Application-shaped classes under `<feature>/models/` — promote up

The self-separation gate (§3.6.1) is **scoped to files inside `<feature>/operations/`**. It does **not** apply to non-model classes under `<feature>/models/`. Do not lift the gate's "self-separated, no relocation needed" reasoning to a model-layer file by analogy — that's how application-layer leaks get rubber-stamped under a models-first banner.

When a non-model class under `<feature>/models/` is **structurally an application service**, the right destination is `<feature>/operations/` (or a specialization layer — `<feature>/ai/`, `<feature>/integrations/`, `<feature>/delivery/`). Naming the class under a `<concept>/` namespace doesn't make it domain. Triggers:

- HTTP client wrapping (`urllib.request`, httpx, requests, urllib).
- Third-party SDK wrapping (`Stripe.`, a Slack SDK, boto3, a Twilio SDK, …).
- **LLM/AI SDK wrapping** (`the installed LLM SDK`, `OpenAI`, `Anthropic`, …) → `<feature>/ai/`, see Phase 2.1.
- Multi-step orchestration whose body enqueues jobs (`*Job.perform_(now|later)`) or calls mailers/deliveries (`*Mailer.`, `.deliver_(now|later)`).
- Transport/broadcast wrappers (`configured_channel_layer.group_send`, AnyCable, pub-sub primitives).

**Concrete practical cost — name it in the report.** The class pulls cross-layer dependencies (HTTP, LLM SDKs, AnyCable, third-party mechanisms) into the Domain-layer autoload graph and into every model-spec boot. Moving it to `<feature>/operations/` (or the specialization layer) eliminates that pull and lets the Domain layer's test suite run without those dependencies stubbed.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "ContextVar|threading.local|request\.|HttpRequest|render\(|redirect\(" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

#### 3.6.5 Thin SDK / broadcast wrappers — delete, hoist, or promote (in that order)

When a class or module exists only to wrap a single SDK call (`configured_channel_layer.group_send`, `provider.generate`, `OpenAI.Client#chat`, `Stripe.Charge.create`) with no error policy beyond what the SDK already provides, no signing logic, no batching, no auth refresh, and no domain rule — the wrapper adds **no value**. Diagnose as **"thin SDK wrapper, no value-add"** and recommend in this order:

1. **Delete** the wrapper and call the SDK directly at the call site. Best when the wrapper is a one-line passthrough (`def broadcast(stream, payload) = configured_channel_layer.group_send(stream, payload)`).
2. **Hoist** the genuinely shared concern (stream signing, payload shaping, prompt formatting) into a `Broadcastable` / `Promptable` **concern** or a base-class method on the consumer — not a separate wrapping object. A one-helper concern beats a one-method module.
3. **Promote** to `<feature>/operations/` (or `<feature>/ai/` for LLM, `<feature>/integrations/` for HTTP) only when the wrapper *does* add a real policy worth keeping: retry beyond the SDK's, multi-step protocol, auth refresh, request signing, rate-limit accounting.

**Verify before recommending the wrapper stay.** Check the SDK's docs (use the framework-docs-researcher or context7 if available) for what it already provides. Examples to call out specifically:

- Inspect the installed SDK retry and timeout settings before adding another retry layer. A wrapper with a distinct idempotency or error policy may be justified; do not claim a package has a feature without checking its version.
- `configured_channel_layer.group_send` is already the public API. Wrapping it to add nothing but a renamed method (`Cable.broadcast(stream, payload)`) is dead weight — recommend deletion + direct call, or a `Broadcastable` concern with `signed_stream_for(record)` if signing is the shared concern.

The tell for "no value-add":

- The wrapper method body is one line that calls the underlying SDK.
- The retry/exception/timeout policy duplicates what the SDK already configures.
- Configuration-style code (`configured?`, `api_key`) lives in the wrapper instead of in a `*Config` class — surface the misplacement; that part belongs in `config/configs/`.

When recommending deletion or relocation, **always quote the underlying SDK's docs** for the feature the wrapper claims to add. "the installed SDK documents this retry policy (versioned link)" is a stronger recommendation than "this wrapper looks thin".

### 3.7 Peer-File Detection

When a service cluster is detected, scan adjacent layers for peer files — workers, jobs, model class methods — that wrap or re-implement the cluster's logic.

#### 3.7.1 Anemic peer Workers/Jobs — check cardinality

When a service cluster is detected, scan `<feature>/tasks/` and `<feature>/tasks/` for peer files matching the cluster's naming pattern. Distinguish cardinality:

- **N services, N workers (1:1 peer wrappers, ≤5 LOC each)** → inspect each boundary. Keep a thin worker if it owns serialization, retries, execution authority or queue registration. Remove only redundant indirection; do not generate implicit async methods.
- **N services, 1 shared worker parameterized by payload** → exemplar; the worker is the cluster's deferral primitive, factored correctly. Surface as a **positive anchor**, not a smell.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "transaction.atomic|on_commit|def .*task|urllib|requests|httpx|openai|anthropic|send_mail" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

#### 3.7.2 Django model class-method orchestrators

Detect Django models with `class << self` blocks containing ≥5 sibling methods of the form `send_*` / `trigger_*` / `dispatch_*` / `notify_*` / `remove_*_async` / `*_without_delay`, where bodies enqueue workers or call services. Surface as a finding distinct from "non-model class in <feature>/models/" — the recommendation is *"consolidate trigger logic into the corresponding abstraction; collapse to one dispatcher or direct call sites."*

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def |dataclass|Protocol" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

### 3.8 Test & Specification Audit

Many cluster-level test points are already raised in Phase 2.3 (sub-section 7c); this section characterizes **the codebase as a whole** and surfaces issues that don't fit a single cluster.

#### 3.8.1 Test convention discovery

Look at `tests/` (or `tests/`) and answer:

- **Coverage** — what fraction of services have a corresponding spec? (Many services with no spec is itself a finding.)
- **Test support helpers** — inspect tests/conftest.py for cohesive fixtures and domain-specific assertion helpers. Recommend extraction only for actual repeated setup.
- **Stubbing style** — use monkeypatch or unittest.mock at actual infrastructure boundaries; preserve explicit inputs and failure behavior.
- **Interface stubbing** — when caller specs stub services, do they all stub the same verb (e.g., `.call`)? If not, that's a downstream effect of a weak call-interface convention.
- **Result discipline** — tests should assert documented typed values or narrow exceptions; optional results must be an explicit contract.

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "def test_|pytest.fixture|monkeypatch|mock.patch|assert " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

**Important — what to recommend, what not to recommend:**

- **Shared fixtures** collect genuinely common setup and remain isolated from mutable state in other tests.
- **Focused pytest assertions** fit uniform specializations: exact query rows, policy booleans, provider payloads and declared failures.
- **Focused fixture setup** that leans on a shared abstraction (e.g., a fixture supplying a configured fake provider) is appropriate.
- **Parametrized tests across heterogeneous operations are not appropriate.** Share cases only when each implementation promises the same contract, such as interchangeable policy or provider adapters.

#### 3.8.2 Specification-test sweep

For 5–8 representative services (mix of cluster-detected and standalone), open the spec and read the `describe`/`context` block names. Classify each context by what it actually verifies:

- **Orchestration** (correct collaborators called, transaction boundaries) — appropriate for a service.
- **Domain rule** (validations, business rules, state transitions) — should live in a model spec.
- **Presentation/HTTP** (params parsing, response codes, redirects) — should live in a controller/request spec.
- **Side-effect plumbing** (mailer/job calls counted, Slack stubbed) — usually wants a delivery or job spec.

In the report, list the services whose specs are dominated by non-orchestration concerns. Each such case is a concrete refactor target that produces an immediate test-quality win.

#### 3.8.3 Test smells that justify refactors

| Smell | How to detect | What it signals |
|---|---|---|
| Heavy controller-stack setup in service specs | Django Client setup in every pure domain test | Service is doing presentation work; tests are slow and brittle |
| Repeated mailer/job/Slack stubbing across cluster | Same provider mock setup in 5+ tests | Cluster wants to be a delivery — extraction enables focused delivery assertions |
| Request doubles in operation tests | grep | Service accepts a request — fix the layer leak first |
| Duplicate model-rule coverage | The same validation tested in `<Service>_spec` and `<Model>_spec` | Domain logic is in services AND model — usually a cue that the service is doing the model's job |
| Unparameterized stubbing of own services (`.with` missing) | a mock accepting arbitrary args without assertions | Call interface non-uniform OR service does too many things to constrain inputs |
| No specs at all in the cluster | Coverage check | The cluster's responsibility is unclear enough that nobody knew what to test — a *strong* promotion signal |

For each smell encountered, name the cluster or files; do not list smells that don't apply.

#### 3.8.4 Stating the test win for each recommendation

Every recommendation in the report (under **Top 3 Actions** and **Recommendations**) must include a one-line **Test win** indicating what specifically improves: faster specs, fewer stubs, framework matchers gained, duplicate coverage removed, layer leak closed. If no test win is identifiable, the recommendation is design-only — call that out so the user can weigh it accordingly.

### 3.9 Anemic-Model Risk

The inverse failure mode. For each model heavily referenced from `<feature>/operations/`:

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "^class |^def |^    def " --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

For each top model:

1. Open `<feature>/models/<model>.py`.
2. Count **substantive method definitions** — exclude:
   - Declarative model fields, relationships, Meta options and enum choices.
   - Single-line aliases / accessors / pure delegations.
3. **Flag as anemic** if ≥10 services touch the model AND the substantive method count is fewer than 3.

For each anemic model, surface one concrete service example whose body manipulates the model's attributes — that's the domain logic that escaped the model.

### 3.10 Target Architecture Signals (positive markers)

Promoted specializations are healthy signals. Report them as a **strength**, not silence them. Each folder gets one of three states (✓ healthy / ⚠ under-used / ✗ absent), not a binary present/missing.

| Folder to check | Contract | Healthy | Needs investigation |
|---|---|---|---|
| `<feature>/forms/` | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |
| `<feature>/queries/` | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |
| `<feature>/policies/` | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |
| `<feature>/delivery/` | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |
| `<feature>/presentation/`, `web/`, `web/src/components/` | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |
| `<feature>/operations/` | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |
| `<feature>/integrations/` | Explicit callable or native Django/React type | Cohesive, used contracts with tests | Incompatible contracts or duplicated responsibilities; a base class is optional |

```bash
# Scope to the feature packages found in pyproject.toml and settings first.
rg --files -g "*.py" -g "!**/migrations/**" -g "!**/.venv/**"
rg -n "transaction.atomic|on_commit|def .*task|urllib|requests|httpx|openai|anthropic|send_mail" --glob "*.py" --glob "!**/migrations/**" --glob "!**/.venv/**"
```

#### Promoted but under-used — the "ghost folder"

A folder is a **ghost** when it exists with files but is not actually carrying the role its name promises. Three triggers:

1. **Sparse adoption** — folder exists with <3 files in a codebase large enough to have produced more (e.g., `<feature>/queries/` has 2 files in a codebase with 500+ models).
2. **Repeated machinery** — files repeat the same stable responsibility. Lack of a base class is not evidence; identify concrete repeated code and consumers.
3. **Same-shape cluster hidden elsewhere** — folder exists at low file count while a same-shape cluster (≥5 candidates) lives under `<feature>/models/` / `<feature>/operations/` / `app/lib/`. The folder was promoted *as a convention* but the team forgot to migrate the real candidates into it.

The ghost state is more actionable than "absent". When `<feature>/queries/` is absent, the report says "consider extracting a query layer" — generic advice. When `<feature>/queries/` is a ghost (2 files, duplicated query contracts, 38 query candidates hiding under `<feature>/models/`), the report says **"the folder already exists — name the decision: grow it into the real layer (migrate the 38 candidates and add `query function`) OR fold it back and delete the folder. Don't leave it as a ghost."**

Surface ghosts in the Codebase Insights → Verdict bullet (use `⚠` between `✓` and `✗`), and in the Specialization clusters proposal block when the cluster's destination is a ghost folder. The decision the team needs to make — **grow the ghost or fold it** — becomes its own recommendation.

A ghost is not a failure; it's an unfinished move. Naming it as such gives the team the choice the original promotion never resolved.

#### Architecture tier verdict

| Tier | Condition |
|---|---|
| **Mature decomposition** | Operations stay focused; established specializations have clear tested contracts |
| **Mature decomposition (models-first variant)** | Cohesive models and explicit feature operations provide clear boundaries without global layer folders |
| **Mixed** | Some specializations promoted, others still in services |
| **Pre-decomposition** | Repeated incompatible responsibilities accumulate in one undifferentiated operations area |

In a "Mature decomposition" report, the recommendations should suggest at most fine-tuning — not refactoring. Celebrate the state.

---

## Reporting Principles

- **Conditional sections.** Do not include a section if there are no findings. No "✅ No issues found" filler.
- **Concrete evidence over generic advice.** Cite specific files, line numbers, and percentages. "Mixed parameter style (keyword-only parameters 64%, kwargs 28%, positional 8%)" beats "establish parameter conventions".
- **No vague recommendations.** Every recommendation must be specific enough to act on without further interpretation. "Add a CI guard" without showing the rule pattern, "introduce a shared abstraction" without surveying the machinery to hoist, "consolidate test frameworks" without naming files — drop these entirely rather than including them. A vague item dilutes the concrete ones around it. If the analysis can't get specific (data missing, scope too large, etc.), say so explicitly instead of waving at it.
- **Insights vs. recommendations are structurally separated.** Pure observations (counts, leaks, smells, hub services, dependency facts) live under `## Codebase Insights`. Concrete proposals (the per-cluster proposal blocks, naming refactors, cross-cutting items) live under `## Recommendations`. The two never share a paragraph.
- **Order: TL;DR → mirror → Top 3 Actions → Recommendations → Codebase Insights → Next Steps.** Recommendations come *before* the supporting observations — a reader who only reads the first half of the report should see the proposals, not the diagnostic data underneath them. Insights are the audit trail; recommendations are the headline content.
- **Top 3 Actions is a thin index, not a recap.** Each action is one short imperative sentence (the *what*) plus a single pointer (`→ Recommendations § Specialization clusters → *Importer`). No "Why" prose, no library options, no test/design win mini-essay — those all live in the per-cluster proposal block the pointer leads to. Duplication kills skimmability.
- **The empirical mirror is exactly one sentence and always gives a definition.** "In this project, a Service Object is …" states the inferred design pattern in plain prose — no code, no numbers, no percentages. Even when no convention has emerged, name the pattern that *has* — typically "any Python callable placed under `<feature>/operations/`". Never write "not defined" or "no convention"; that's a refusal, not a definition. Save the metric bullets for `## Codebase Insights → Conventions`.
- **The contract sub-section is a Python code block, not a prose table.** Sub-section 4 of the cluster proposal block declares the abstraction's shape as a small Python snippet (shared abstraction with declarative DSL, abstract method placeholders, one concrete subclass example, peer-use call sites). The reader takes the code as the contract.
- **Don't push placement.** For every cluster, mention both nesting (`<feature>/operations/queries/`) and promotion (`<feature>/queries/`); let the user decide.
- **Don't push naming when the classification is ambiguous.** When a folder or cluster could plausibly fit more than one canonical pattern (facades vs. presenters, resolvers vs. queries, managers vs. coordinators), the actionable diagnosis is the *missing contract* — shared abstraction, shared interface, documented role — which holds regardless of which name wins. Surface the candidate names as options; recommend the convention introduction; do not pick the new folder name. A confident rename is justified only when (a) the canonical pattern is unambiguous (e.g., `app/temporal/` → `app/workflows/` because no other layer claims Temporal.io) AND (b) the rename brings concrete affordances beyond what "introduce a shared abstraction" already provides (a framework convention activating, a library binding, an existing base under the new name).
- **Codebase-faithful contracts.** The Python contract block in §4 of each cluster proposal preserves the codebase's existing mixins, parameter library, and call interface. Do not silently substitute the textbook canonical form (a parameter DSL, a monadic framework, invented callable mixins) for what the team actually uses — the proposal must be migratable from the codebase's current building blocks. Surface canonical alternatives as one-line comments in the code or in §5 Library options, never as the headline contract. The exception: when the codebase's own convention is itself the diagnosis (multiple competing bases), the contract proposes the consolidating shape and names what's being collapsed.
- **Promoted but under-used folders are their own state.** Specialization folders get three verdicts (✓ healthy / ⚠ under-used "ghost" / ✗ absent), not a binary present/missing. A ghost — folder exists with <3 files OR no shared base OR same-shape candidates hidden elsewhere — is more actionable than absence: the recommendation names the decision *"grow into a real layer or fold back and delete"* instead of "consider extracting".
- **Recommend the abstraction layer, not the library.** The report says "extract a notification layer", not "install a delivery framework". When a concrete library is helpful for illustration, list 2+ alternatives and mark one as the example used to make the suggestion tangible. The user picks the implementation; the command picks the layer. Sketch-with-X follow-ups go in the **Next Steps** section, not inline in the recommendation.
- **Recommend the contract, not just the layer.** Phase 2.3 sub-section 4 names class-name shape, method names, return shape, and cross-boundary conventions. A named function is one valid contract; specializations often want richer verbs (resolve for queries, can_access for policies, deliver for notifications, import_records for importers).
- **Show, don't just tell.** For promote-up clusters with ≥6 files, include the "Adding a new feature" before/after walkthrough. Demonstrating the pull is the proposal payoff that diagnoses cannot match.
- **Tests are first-class evidence.** Every cluster, every recommendation, every convention finding must connect to a test consequence — current pain (slow specs, repeated stubs, layer leakage) and/or future affordance (matchers, shared contexts, focused setup). A recommendation without a test win must be flagged as design-only.
- **The specification test is the headline diagnostic.** When a spec's contexts describe responsibilities outside its layer, that's the most concrete signal a refactor is justified. Quote actual `describe`/`context` lines as proof.
- **Shared examples across heterogeneous services are out of scope.** Recommend shared *contexts* and custom matchers tied to specific specializations; never blanket one universal service contract test.
- **Promote-up and demote-down are equally valid moves.** Many "services" should disappear into a value object or a delegate object. The proposal block treats demotion as a first-class proposal, not a footnote.
- **Healthy clusters are positive anchors, not silence.** When a cluster scores well on layer-hygiene axes (shared base, single shared deferral surface, infra separated, centralized opt-out, specs at the right level), explicitly surface it as an exemplar:
  1. A one-paragraph TL;DR naming it as the healthy reference.
  2. A side-by-side comparison table against any sibling cluster being told to refactor — same axes, ✓/✗ visible at a glance.
  3. A line: *"the shape this sibling proposal is asking for is exactly what *this cluster* already does."*
  4. Per-event mapping if a unification is plausible.

  This validates good work and gives the team a concrete in-codebase reference.
- **Articulate benefits, not just shape.** Every cluster proposal must include a net-benefit paragraph: the concrete current ritual (the actual N steps today), the post-refactor ritual (the 1–2 steps it becomes), which spec layers stop testing things they shouldn't, what becomes reusable that today is locked inside service bodies. Phase 2.3 sub-section 7 is where this lands; do not omit it.

### What the report body must NOT contain

- **No author name-drops.** End users do not know who Swett, Avdi, Fowler, Metz, Evans, DHH, etc. are. Do not write "by Swett's rule", "the Avdi smell", "per Fowler's anemic-domain-model anti-pattern", "Sandi Metz says". State the rule directly. If the source matters, it goes in the "Read more" section at the end.
- **No bare chapter-number references.** Do not write "per Chapter 5", "Chapter 6's domain services", "the book recommends". Either state the rule directly without attribution, or include the source in "Read more".
- **No buzzwords without explanation.** "DDD ubiquitous language" → "the name comes from the business glossary". "Specification test" is a defined concept the report uses; that's fine, but explain the first time it appears.

### Optional tail: "Read more"

When the report leans on specific external sources to justify rules, include a short "Read more" section listing them. When only general principles were applied, **omit the section entirely** — don't pad with the canonical book + two blog posts as a default.

If included, format as a short list with one-line context per link:

```markdown
## Read more

- *Layered Design for Ruby on Rails Applications* — the layered-architecture rules and the waiting-room metaphor. [Packt](https://www.packtpub.com/en-us/product/layered-design-for-ruby-on-rails-applications-9781801813785)
- "Service Objects" — case against service-shaped procedures. [avdi.codes/service-objects](https://avdi.codes/service-objects/)
```

## Output Format

The report opens with **TL;DR**, the empirical mirror, and a thin **Top 3 Actions** index. **Recommendations** (the per-cluster proposal blocks — the headline content) come next, followed by **Codebase Insights** (the supporting evidence) and **Next Steps**. Recommendations and insights live in separate top-level sections — never mixed in the same paragraph.

```markdown
# Service Object Analysis — <project name>

## TL;DR

A single sentence stating the next move — concrete enough that the team could start work on it tomorrow. No prefix ("Monday move:", "Headline:", etc.) — just the statement. Example:

> Extract a delivery layer for `pb_slack/messages/*Formatter` — the single highest-leverage move; closes the layer leak and unlocks per-channel test isolation.

Then a one-paragraph diagnosis: tier verdict, key strengths, key gaps, the forces at play. No actions — state-of-the-world only.

## In this project, a Service Object is …

**Exactly one sentence** synthesizing the team's implicit design pattern, with no code, numbers, or percentages — those live in Codebase Insights → Conventions. See Phase 1.2 for examples and rationale.

## Top 3 Actions

A thin index — each action is **one short imperative sentence** (the *what*) plus a **single pointer** to the detailed proposal below. No "Why" prose, no library options, no test/design win mini-essay — those all live in the Recommendations section the pointer leads to. The reader skimming this list should know which three things matter and where to read about each.

1. **Consolidate the importer/loader cluster into a unified data-import layer.** → Recommendations § Specialization clusters → `*Importer` / `*Loader`.
2. **Establish a single call convention across the rest of `<feature>/operations/`.** → Recommendations § Other recommendations.
3. **Fix the `<feature>/operations/stripe_payment.py` presentation leak.** → Recommendations § Other recommendations.

(If a fourth action is genuinely co-equal in priority, surface it; the "Top 3" framing is a budget, not a hard cap.)

---

## Recommendations

Concrete proposals. Each rests on observations gathered in Codebase Insights below; cross-references inline where useful. If a recommendation can't be made specific (e.g., "add a CI guard" without showing the rule pattern), it doesn't appear here — drop it rather than wave at it.

### Specialization clusters

For each cluster, the 8-part proposal block from Phase 2.3:

#### `*Query` / `*Finder` cluster (14 services) — promote: extract a query layer

**1. Cluster identity.** 14 services under `<feature>/operations/queries/` matching `*_query.py` / `*_finder.py`. Sample: `users/active_query.py`, `payments/recent_finder.py`. Destination: promote-up to a query layer.

**2. Current pain.** (concrete observations with file:line)

**3. Specification-test verdict.** (1–2 quoted `describe`/`context` lines)

**4. Suggested interface / contract.**

```python
def active_users(users, *, since):
    return users.filter(is_active=True, last_seen_at__gt=since)

result = active_users(authorized_users(actor), since=last_week)
# A base query class is not necessary to compose QuerySets.
```

**5. Library options.** Hand-rolled Python objects over `QuerySet`, `validated QuerySet filters` for parameter-driven scoping, or `QuerySet`-backed filter objects.

**6. Shared machinery.** Surveyed 5 cluster files. Common: tenant scope wrapping, parameter validation, default scope chaining. The base hoists `param :scope`, `merge`, and the abstract `QuerySet return contract` contract.

**7. Benefits showcase.**

a. **Deduplication.** ~40 LOC saved across the cluster (parameter declarations + merge boilerplate currently repeated in 11/14 files).

b. **Common issues solved.** Tenant scoping is currently inconsistent — 9/14 files apply `ambient_tenant`, 5 don't. Required tenant parameters and scoped QuerySets make this uniform.

c. **Test simplification.** Focused query assertions replace the 9 specs that currently five unrelated User fixtures to test what's effectively User.objects.filter(is_active=True).

d. *(promote-up cluster ≥6 files)* **"Adding a new feature" walkthrough.**

```python
# Before extraction: a stable cohesive query is already small.
def recent_signups(users, *, since):
    return users.filter(date_joined__gt=since).order_by("-date_joined", "pk")
# After: retain this function or move it into an existing custom QuerySet.
# Count real boilerplate removed before introducing an query function type.
```

e. **Cross-boundary conventions unlocked.** Caller specs converge on an explicit query-function boundary; controllers compose a scoped QuerySet passed to a query function uniformly.

**8. Placement (your call).** Nest under `<feature>/operations/queries/` (minimal) OR promote to `<feature>/queries/` (first-class).

#### Calculators (~25 files in `<feature>/models/`) — demote: shape the domain-services sub-layer in place

(Structure identical to a promote-up cluster; sub-section 7d — the walkthrough — is omitted for demote clusters.)

### Naming refactors (from §3.3)

**`-er` suspects (5)** — (list)
**Tautological method/class pair (2)** — (list)
**Domain-method candidates (3)** — (list with specific moves)
**Module-function candidates (4)** — (list)

### Other recommendations

- (cross-cutting items — e.g., return-value convention, anemic-model restoration, layer-leak fixes that don't fit a cluster)

---

## Codebase Insights

Pure observations about the codebase — the supporting evidence the recommendations above rest on. No proposals live in this section. Hub services, fan-in lists, and similar diagnostic data are observations only; they don't require a recommendation to be worth surfacing.

### Verdict
- Services: N files, L LOC (X% of app/)
- Architecture tier: **Mature decomposition** | Mature decomposition (models-first variant) | Mixed | **Pre-decomposition** | Repeated incompatible responsibilities accumulate in one undifferentiated operations area |
- Promoted specializations: forms ✓ | queries ⚠ (ghost — 2 files, no base, ~38 query-shaped candidates hide under `<feature>/models/`) | policies ✓ | deliveries ✗ | presenters ✗
- Convention strength: Strong | Mixed | Weak ("bag of random objects")
- Organization: Healthy | Sprawling | Bag of random objects
- Test convention strength: Strong | Mixed | Weak (spec coverage X%, no shared contexts/matchers, ...)
- Naming smells: K services flagged
- Implicit workflows: J chains of length ≥3
- Specialization opportunities: K clusters (M promote / N demote)
- Layer-hygiene issues: M
- Anemic-model risk: P models
- Service-like models: Q files (split: domain D / application A)

### Conventions (deviation report from 1.2)
- (per-axis findings)

### Organization
- (sub-namespace counts; mega-namespace flags; vendor-folder flags)

### Layer-Hygiene
- (presentation deps, Current usage, sinkhole findings)

### Implicit Workflows
- (chains, hub services — pure observations)

### Service-Like Classes in `<feature>/models/`
- (domain candidates list; application candidates list — purpose test applied)

### Test & Specification
- (coverage; conventions; specification-test sweep findings; test smells)

### Anemic-Model Risk
- (top models with low method counts)

### (When applicable) Risks the team has accepted by keeping `<feature>/operations/` absent
- (10-item list for models-first stance)

---

## Next Steps

Follow-up prompts you can run when ready to dig deeper. Include only items that follow from actual recommendations above — don't pad.

- **Sketch `query function`** based on the surveyed machinery. Run: *"Sketch query function for the *Query cluster."*
- **Sketch `ApplicationImporter`** for the importer cluster. Run: *"Sketch ApplicationImporter for sera."*
- (other follow-up prompts)
```

## Related

- [Service Objects pattern](../references/patterns/service-objects.md)
- [Query Objects pattern](../references/patterns/query-objects.md)
- [Value Objects pattern](../references/patterns/value-objects.md)
- [Collaborator / Delegate Objects pattern](../references/patterns/collaborator-objects.md)
- [Service Objects anti-patterns](../references/anti-patterns/service-objects.md) — bag of random objects, anemic models, premature abstraction
- [Specification test](../references/core/specification-test.md)
- [Current attributes](../references/topics/current-attributes.md)

Companion workflows (linked from SKILL.md): the architecture-analysis workflow runs first for the wide view; the god-object and callback-analysis workflows go deeper on those specific dimensions.
