# Extract God Object with Associated Objects

Decompose a sprawling `User` model into focused collaborators using the associated-objects pattern.

## Before

```python
# Before: these independent responsibilities accumulate on the user model.
class User(AbstractUser):
    def invoice_history(self, billing_client):
        return billing_client.list_invoices(customer_id=self.billing_customer_id)

    def unread_notifications_count(self):
        return self.notifications.filter(read_at__isnull=True).count()

    def notification_preferences(self):
        return {"email": self.email_notifications, "push": self.push_notifications}
```

## After

```python
from dataclasses import dataclass


class User(AbstractUser):
    # Authentication remains with Django; notification settings have their own data owner.
    pass


class NotificationSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    digest_frequency = models.CharField(max_length=10, default="daily")


@dataclass(frozen=True)
class Billing:
    customer_id: str
    client: BillingClient

    def invoice_history(self):
        return self.client.list_invoices(customer_id=self.customer_id)
```

Billing API calls are explicit application/infrastructure work, never model
properties. Subscription mutations need a separate idempotency and reconciliation
contract; SQL and a payment provider cannot share a database transaction.
