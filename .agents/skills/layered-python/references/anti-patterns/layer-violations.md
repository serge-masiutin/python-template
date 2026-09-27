# Layer Violations

Cross-layer dependencies that break unidirectional data flow.

## Contents

- Current Attributes in Models
- Request Objects in Services
- Notifications in Models
- Business Logic in Controllers

## Current Attributes in Models

**Problem:** Models depend on presentation-layer context.

```python
class Post(models.Model):
    def delete(self, *args, **kwargs):
        self.deleted_by = current_user.get()
        return super().delete(*args, **kwargs)
```

**Issues:**
- Background jobs lose Current context (silent bugs)
- Callbacks can overwrite Current mid-iteration
- Hidden dependency makes testing harder
- Violates no-reverse-dependencies rule

**Fix:** Use explicit parameters.

```python
class Post(models.Model):
    def mark_deleted(self, *, actor, at):
        self.deleted_by = actor
        self.deleted_at = at
```

## Request Objects in Services

**Problem:** Application layer depends on presentation layer.

```python
def handle_event(request):
    event_type = request.headers["X-Event-Type"]
    payload = json.loads(request.body)
    dispatch_event(event_type, payload)
```

**Fix:** Extract value object in controller, pass to service.

```python
def github_callback(request):
    event = parse_verified_github_event(request)
    handle_event(event=event)
    return HttpResponse(status=204)


def handle_event(*, event):
    issue = Issue.objects.get(provider_id=event.issue_id)
    issue.apply_event(event)
    issue.save()
```

## Notifications in Models

**Problem:** Model triggers notifications, crossing into application layer.

```python
class License(models.Model):
    def prolong(self, *, until):
        self.expires_at = until
        self.save(update_fields=["expires_at"])
        send_purchase_email(self.pk)
```

**Issues:**
- Domain layer depends on application layer (reverse dependency)
- Model has side effects beyond state management
- Harder to test model in isolation
- Notification may fire unexpectedly from different call sites

**Fix:** Trace the call chain, move notification to existing orchestrator.

```python
class License(models.Model):
    def prolong(self, *, until):
        self.expires_at = until


@transaction.atomic
def apply_paid_invoice(*, invoice):
    license = License.objects.select_for_update().get(pk=invoice.license_id)
    license.prolong(until=invoice.coverage_end)
    license.save(update_fields=["expires_at"])
    transaction.on_commit(partial(send_purchase_email, license.pk))
```

**Resolution process:**
1. Find the caller (controller, service, job)
2. If orchestrator exists → move notification there
3. If no orchestrator → suggest service/form/controller based on context

## Business Logic in Controllers

**Problem:** Presentation layer doing domain work.

```python
def create_order(request):
    form = OrderForm(request.POST)
    if not form.is_valid():
        return invalid_form(request, form, destination="order-new")
    order = form.save(commit=False)
    order.total = sum(item.price * item.quantity for item in form.cleaned_data["items"])
    if order.customer.is_vip:
        order.total *= Decimal("0.90")
    order.total += shipping_price(order)
    order.save()
    return redirect_303("order-detail", order_id=order.pk)
```

**Fix:** Move domain logic to model, orchestration to service if needed.

```python
class Order(models.Model):
    def calculate_total(self, *, items, shipping):
        subtotal = sum((item.subtotal() for item in items), Decimal("0"))
        if self.customer.is_vip:
            subtotal *= Decimal("0.90")
        self.total = subtotal + shipping


@transaction.atomic
def place_order(*, customer, items, shipping):
    order = Order(customer=customer)
    order.calculate_total(items=items, shipping=shipping)
    order.full_clean()
    order.save()
    transaction.on_commit(partial(send_order_confirmation, order.pk))
    return order
```
