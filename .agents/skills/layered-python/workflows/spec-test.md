# Spec-Test Workflow

Run the specification test on files to evaluate layer responsibility alignment.

The specification test works by generating a **test skeleton** — the describe/context structure that would be needed to fully test the code. This skeleton makes layer violations immediately visible: if you see `context "when HTTP response fails"` inside a domain model spec, something is wrong.

## Contents

- [Process](#process)
- [Layer Primary Responsibilities](#layer-primary-responsibilities)
- [Output Format](#output-format)
- [Existing Test Analysis](#existing-test-analysis)
- [Extraction Recommendations](#extraction-recommendations)
- [Example](#example)
- [Automation Level](#automation-level)

## Process

1. **Read target file(s)**
2. **Identify architecture layer** (Presentation, Application, Domain, Infrastructure)
3. **Generate test skeleton** — describe/context blocks covering all code paths, annotated with ✓/⚠️/✗ markers
4. **Search for existing tests** — look for corresponding spec/test files; if found, annotate the actual test structure
5. **Recommend extractions** — concrete suggestions for misplaced responsibilities

## Layer Primary Responsibilities

| Layer | Primary Concern | Should Handle | Should NOT Handle |
|-------|-----------------|---------------|-------------------|
| Presentation (Controller) | HTTP handling | Auth, params, response codes, redirects | Business logic, calculations |
| Application (Service) | Use-case orchestration | Coordinating domain objects, transactions | Domain rules, HTTP concerns |
| Domain (Model) | Business rules | Validations, calculations, state transitions | Notifications, HTTP, external APIs |
| Infrastructure | Technical implementation | Persistence, external communication | Business rules |

## Output Format

```markdown
# Specification Test: [FileName]

**Layer:** [Identified layer]
**Primary Responsibility:** [Layer's primary concern]

## Test Skeleton

Generate the describe/context structure that would be needed to fully test this code.

**Skip configuration — only describe behavior:**
- Do NOT include associations, simple validations, enums, or other declarative
  configuration. Tests for a ForeignKey declaration or enum choices alone are rarely
  useful and clutter the skeleton. Only include validations if they contain
  non-trivial logic (custom validators, conditional rules, cross-field checks).
- Focus on public methods and their behavioral edge cases.

**Authorization methods** (e.g., `accessible_to`, `can_edit`, policy-like checks):
- Flag as ⚠️ by default. In projects with a dedicated authorization layer
  (explicit policy functions or permission adapters), these belong in policy objects, not models.
- Only mark ✓ if the project clearly has no authorization abstraction and
  keeps access rules in models by convention.

Every context must be annotated:

- ✓ — belongs in this layer
- ⚠️ — borderline, could stay but signals a design smell
- ✗ — does NOT belong in this layer (layer violation)

` ` `text
ClassName:
  - #method_name
    - when [scenario]           # ✓ [Layer concern]
    - when [scenario]           # ✗ [Wrong layer] — [brief why]
` ` `

After the skeleton, add a short summary: how many contexts total, how many ✓, ⚠️, ✗.

## Existing Test Analysis

Search for existing test files for the target code. Use the project's test
framework conventions:

- pytest: `tests/test_*.py` or existing project discovery rules
- Django TestCase: `<feature>/tests.py` or `tests/test_*.py`

If tests exist:

1. Show the **actual** describe/context structure (extracted from the file)
2. Annotate each context with ✓/⚠️/✗ markers (same as the skeleton)
3. Highlight **symptoms of layer violations** in the test code:
   - Heavy mocking/stubbing of external services inside a model spec
   - Complex setup (factory chains, request stubs) for what should be simple unit tests
   - Callback bypass workarounds (bulk update or disconnected signal receivers) in test setup
   - Tests that are slow/brittle because they test across layer boundaries

If no tests exist, state that and note what the skeleton above reveals about testability.

## Extraction Recommendations

For each ✗ or ⚠️ item:

1. **[Responsibility]** → Extract to [target]
   - Current location: `file:line_range`
   - Suggested pattern: [pattern name]
   - Brief code sketch (keep short)
   - **Test impact:** Show how tests change after extraction. The key benefit:
     the original object's test can now mock/stub the extracted component and
     only verify it was invoked with the right input — all the ✗ contexts
     move to the extracted component's own test. Show both sides: what the
     original test becomes (simpler, mocking the extraction) and what the new
     test covers (the moved logic, tested in isolation).
```

## Example

Input: `<feature>/views/orders_controller.py`

```python
def create_order(request):
    # Anti-example: transport owns price calculation, external calls and persistence.
    order = Order(customer=request.user)
    order.total = sum(item.price * item.quantity for item in validated_items(request))
    if order.customer.is_vip:
        order.total *= Decimal("0.90")
    order.total += Decimal("10")
    order.save()
    send_order_confirmation(order.pk)
    warehouse_client.create_order(order)
    return redirect_303("order-detail", order_id=order.pk)
```

Output:

```markdown
# Specification Test: OrdersController

**Layer:** Presentation
**Primary Responsibility:** HTTP request/response handling

## Test Skeleton

` ` `text
- POST /orders
  # --- HTTP / Auth ---
  - when user is not authenticated          # ✓ Presentation — access control
  - when user is authenticated           # ✓ Presentation — access control
    - when order params are valid         # ✓ Presentation — param handling
      - creates an order and redirects            # ✓ Presentation — response

      # --- Pricing (domain logic leaked into controller) ---
      - when customer is VIP
        - applies 10% discount                    # ✗ Domain — pricing rule
      - when customer is not VIP
        - charges full price                      # ✗ Domain — pricing rule

      # --- Shipping (domain logic leaked into controller) ---
      - when items weigh over 10
        - adds weight surcharge                   # ✗ Domain — shipping calculation
      - when express shipping selected
        - adds express surcharge                  # ✗ Domain — shipping calculation

      # --- Notifications (application concern leaked into controller) ---
      - sends confirmation email                  # ✗ Application — notification orchestration
      - sends Slack notification                  # ✗ Application — notification orchestration

      # --- External sync (infrastructure leaked into controller) ---
      - syncs order to warehouse API              # ✗ Infrastructure — external API call

    - when order params are invalid
      - renders the form with errors              # ✓ Presentation — error response
` ` `

**Summary:** 12 test contexts — 4 ✓, 0 ⚠️, 8 ✗
Only 33% of what this controller needs testing actually belongs in the controller.

## Existing Test Analysis

Found: `tests/orders_test.py`

` ` `text
- POST /orders
  - when params are valid                 # ✓ Presentation
    - creates the order                           # ✓ Presentation
    - applies VIP discount                        # ✗ Domain — pricing rule tested via HTTP roundtrip
    - calculates shipping for heavy items         # ✗ Domain — requires factory setup for weight
  - when params are invalid               # ✓ Presentation
    - returns 422                                 # ✓ Presentation
` ` `

**Symptoms visible in existing tests:**
- VIP discount test requires creating a user with is_vip=True + items with specific prices — heavy setup for a pricing rule
- Shipping test creates items with specific weights — testing domain math through an HTTP request
- No tests for Slack/warehouse sync — likely untested because setup is too complex at this layer

## Extraction Recommendations

1. **Pricing + shipping** → Order model
   - Current location: `orders_controller.py:7-10, 25-31`
   - Pattern: Explicit model calculation called by the application operation
   ` ` `python
def calculate_total(self, *, items, shipping):
    subtotal = sum((item.subtotal() for item in items), Decimal("0"))
    discount = Decimal("0.9") if self.customer.is_vip else Decimal("1")
    return subtotal * discount + shipping
` ` `
   - **Test impact:** Controller test no longer needs VIP/shipping contexts — just verify the order is saved and response is correct. All pricing/shipping edge cases move to a fast model unit test:
   ` ` `text
   # Controller test (after) — no pricing concerns
   - POST /orders
     - creates the order and redirects # ✓ no VIP setup, no weight setup

   # Model test (new) — isolated, fast
   Order.calculate_total:
     - when customer is VIP
     - when items weigh over 10
     - when express shipping selected
` ` `

2. **Notifications + warehouse sync** → Application layer / background job
   - Current location: `orders_controller.py:14-18`
   - Pattern: explicit delivery + background job
   - **Test impact:** Controller test verifies the delivery/job was enqueued, not that Slack/email/warehouse actually received anything:
   ` ` `text
   # Controller test (after) — mock the side effects
   - enqueues order notifications
     assert_enqueued_with(job: OrderDelivery) { post orders_path, ... }

   # Delivery test (new) — isolated
   Order delivery:
     - sends confirmation email
     - sends Slack notification
` ` `
```

## Automation Level

This workflow runs with mid-to-high automation:

1. **Automatic:** Layer identification, test skeleton generation, annotation
2. **Automatic:** Search for existing tests, structure extraction, symptom analysis
3. **Automatic:** Extraction recommendations with code sketches
4. **Manual input needed:** Only for ambiguous cases or when multiple valid approaches exist
