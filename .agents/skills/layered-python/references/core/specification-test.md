# The Specification Test

## Contents

- The Specification Principle
- Quick Test-Outline Diagnostic
- Layer Responsibilities
- Example: Controller Specification
- Example: Service Specification
- Example: Model Specification
- Cost Consideration
- Detailed Code Audit (3-Step Process)
- Quick Reference

## The Specification Principle

> If the specification of an object describes features beyond the primary responsibility of its abstraction layer, such features should be extracted into lower layers.

The specification test helps identify code that belongs in a different layer by examining what tests would verify.

## Quick Test-Outline Diagnostic

1. **Write test structure** (contexts/describes) without implementation
2. **Examine what the tests verify**
3. **Ask:** Does this test verify the object's primary responsibility?

If a test verifies something outside the layer's primary concern, that code should be extracted.

## Layer Responsibilities

| Layer | Primary Responsibility | Tests Should Verify |
|-------|------------------------|---------------------|
| Presentation (Controller) | HTTP handling | Authentication, authorization, response codes, redirects |
| Application (Service) | Use-case orchestration | Correct domain objects called, transaction boundaries |
| Domain (Model) | Business rules | Validations, state transitions, calculations |
| Infrastructure | Technical implementation | Data persistence, API calls |

## Example: Controller Specification

```text
HTTP test suite:
  missing signature       -> transport authentication
  invalid signature       -> transport authentication
  pull-request rules      -> move detailed cases to operation tests
  issue rules             -> move detailed cases to operation tests
  absent domain user      -> operation contract
```

The business logic tests indicate code that should move to the application or domain layer.

**After extraction:**

```text
HTTP tests: missing, invalid and valid signature; response mapping.
Operation tests: issue, pull-request and absent-user behavior.
Keep one end-to-end case proving the boundary delegates successfully.
```

## Example: Service Specification

```text
Operation tests: transaction outcome, payment failure, inventory failure.
Order tests: maximum discount, minimum total, domain arithmetic.
```

Discount and minimum order rules are domain logic—they belong in the Order model.

## Example: Model Specification

```text
Model tests: validation, total calculation, discount rules.
Delivery operation tests: confirmation intent and delivery failure.
Warehouse adapter tests: request schema and external error mapping.
```

Notification and external sync are not domain responsibilities.

## Cost Consideration

Higher-layer tests are:
- **Harder to write** (more context setup)
- **Slower to execute** (HTTP requests, full stack)
- **More brittle** (depend on more components)

Moving logic to lower layers enables faster, simpler, more focused tests.

| Test Type | Speed | Setup Complexity | Brittleness |
|-----------|-------|------------------|-------------|
| Model/unit | Fast | Low | Low |
| Service | Medium | Medium | Medium |
| Controller/request | Slow | High | High |
| System/integration | Slowest | Highest | Highest |

## Detailed Code Audit (3-Step Process)

### Step 1: List Responsibilities

For the code you're examining, list every responsibility it handles.

Example for `OrdersController#create`:
- Parse order parameters
- Authenticate user
- Authorize order creation
- Validate inventory
- Calculate pricing
- Apply discounts
- Create order record
- Send confirmation email
- Sync to warehouse API
- Return JSON response

### Step 2: Categorize by Layer

| Responsibility | Layer | Belongs in Controller? |
|----------------|-------|------------------------|
| Parse parameters | Presentation | ✓ Yes |
| Authenticate user | Presentation | ✓ Yes |
| Authorize creation | Application | ✓ Yes (or policy) |
| Validate inventory | Domain | ✗ No |
| Calculate pricing | Domain | ✗ No |
| Apply discounts | Domain | ✗ No |
| Create record | Domain | ✗ No |
| Send email | Presentation | ✗ No (not controller's job) |
| Sync to API | Infrastructure | ✗ No |
| Return JSON | Presentation | ✓ Yes |

### Step 3: Extract

Move misplaced responsibilities to appropriate layers:

```python
def create_order(request):
    form = OrderForm(request.POST)
    if not form.is_valid():
        return invalid_form(request, form, destination="order-new")
    order = place_order(actor=request.user, **form.cleaned_data)
    return redirect_303("order-detail", order_id=order.pk)


@transaction.atomic
def place_order(*, actor, items):
    order = Order(customer=actor)
    order.calculate_pricing(items=items)
    order.full_clean()
    order.save()
    DeliveryIntent.objects.create(order=order, event="order_created")
    return order
```

## Quick Reference

**Controller should test:**
- HTTP status codes
- Redirects
- Authentication/authorization
- Parameter handling
- Response format

**Controller should NOT test:**
- Business rules
- Calculations
- State transitions
- External service behavior

**Service should test:**
- Correct objects orchestrated
- Transaction success/failure
- Error handling

**Service should NOT test:**
- Domain validation rules
- Business calculations
- HTTP concerns

**Model should test:**
- Validations
- Business rules
- Calculations
- State transitions

**Model should NOT test:**
- HTTP concerns
- Notification delivery
- External API calls
