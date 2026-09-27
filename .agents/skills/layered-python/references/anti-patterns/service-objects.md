# Service Object Anti-Patterns

Common mistakes when introducing service objects.

## Contents

- Anemic Models
- Bag of Random Objects
- Premature Abstraction

## Anemic Models

**Problem:** All logic moved to services, models become data containers.

```python
def calculate_order_total(order, items):
    order.total = sum(item.price * item.quantity for item in items)
    if order.customer.is_vip:
        order.total *= Decimal("0.90")
    order.save(update_fields=["total"])


def apply_discount(order, discount):
    order.discount_amount = discount.amount
    order.save(update_fields=["discount_amount"])
```

**Fix:** Keep domain logic in models. Services orchestrate, models know their business rules.

```python
class Order(models.Model):
    def calculate_total(self, *, items):
        self.total = sum((item.subtotal() for item in items), Decimal("0"))
        if self.customer.is_vip:
            self.total *= Decimal("0.90")

    def apply_discount(self, *, discount):
        self.discount_amount = discount.amount
```

## Bag of Random Objects

**Problem:** No conventions, each service is unique.

```python
# Bad: unrelated result conventions at the same boundary.
registered = registration.perform(attributes)  # User or None
processed = OrderProcessor.process(order_id)   # Raises domain errors
sent_count = newsletter.run(subscribers)       # Integer
```

**Fix:** Establish conventions.

```python
# Prefer functions or focused callable classes, explicit inputs, and domain errors.
user = register_user(username=username, password=password)
order = process_order(order_id=order_id)
# Both return the resulting domain record and raise documented exceptions.
```

## Premature Abstraction

**Problem:** Creating abstractions before patterns emerge.

```python
class BaseCommand(CommandPattern, ResultMonad, TransactionWrapper):
    pass

class CreateUserCommand(BaseCommand):
    def execute(self):
        return User.objects.create_user(**self.parameters)
```

**Fix:** Wait for patterns to emerge. Start simple.

```python
# Simple persistence needs no service layer at all.
user = User.objects.create_user(username=username, password=password)
# Extract an operation when a real workflow coordinates multiple owners.
```
