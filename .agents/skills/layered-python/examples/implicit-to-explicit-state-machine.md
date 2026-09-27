# Replace Implicit State Machine

Replace ad-hoc timestamp checks with an explicit state machine using explicit transitions and database constraints.

## Before

```python
class Order(models.Model):
    def status(self):
        if self.cancelled_at is not None:
            return "cancelled"
        if self.delivered_at is not None:
            return "delivered"
        if self.shipped_at is not None:
            return "shipped"
        if self.paid_at is not None:
            return "paid"
        return "pending"

    def ship(self):
        if self.paid_at is None or self.shipped_at is not None or self.cancelled_at is not None:
            return False
        self.shipped_at = timezone.now()
        self.save(update_fields=["shipped_at"])
        send_shipping_email(self.pk)
```

## After

```python
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        PAID = "paid"
        SHIPPED = "shipped"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"

    status = models.CharField(max_length=10, choices=Status, default=Status.PENDING)
    shipped_at = models.DateTimeField(null=True)

    def ship(self):
        if self.status != self.Status.PAID:
            raise InvalidTransition("Only paid orders can ship")
        self.status = self.Status.SHIPPED
        self.shipped_at = timezone.now()


@transaction.atomic
def ship_order(*, order_id):
    order = Order.objects.select_for_update().get(pk=order_id)
    order.ship()
    order.save(update_fields=["status", "shipped_at"])
    transaction.on_commit(partial(send_shipping_email, order.pk))
    return order
```

Declare the other allowed transitions with the same guard pattern. Add a database
check for the state domain; `choices` alone is not a database constraint. Historical
timestamps remain audit facts rather than competing sources of current state.
