# Notifications

## Contents

- Summary
- Layer Placement
- Key Principles
- Implementation with explicit delivery
- Without explicit delivery
- Triggering Notifications from State Machines
- Anti-Patterns
- Delivery Patterns

## Summary

Notifications deliver messages through multiple channels (email, SMS, push, in-app). explicit delivery provides a layer of abstraction over delivery mechanisms, making notifications a first-class domain concept.

## Layer Placement

```
┌─────────────────────────────────────────┐
│ Application Layer                       │
│  └─ Delivery classes (what to send)     │
├─────────────────────────────────────────┤
│ Infrastructure Layer                    │
│  └─ Mailers, SMS adapters (how to send) │
└─────────────────────────────────────────┘
```

## Key Principles

- **Delivery abstraction** — separate what from how
- **Channel-agnostic** — same notification, multiple delivery methods
- **Testable** — verify notifications without infrastructure
- **Configurable** — enable/disable channels per notification type

## Implementation with explicit delivery

### Basic Setup

```python
def published_message(*, post, recipient):
    return EmailMessage(subject=f"Your post '{post.title}' is live", body=post.title,
                        from_email=settings.DEFAULT_FROM_EMAIL, to=[recipient.email])

# Format content separately from explicit SMTP/Slack/push adapter calls.
```

### Triggering Notifications

```python
@transaction.atomic
def publish_post(*, post):
    post.publish(at=timezone.now())
    post.save(update_fields=["published_at"])
    DeliveryIntent.objects.create(post=post, event="published")
```

### Conditional Delivery

```python
def publication_channels(*, post, preferences):
    channels = ["email"]
    if post.is_featured:
        channels.append("slack")
    if preferences.push_enabled:
        channels.append("push")
    return channels
```

### User Preferences

```python
def enabled_channels(preferences):
    return [name for name, enabled in [("email", preferences.email_enabled),
                                      ("push", preferences.push_enabled),
                                      ("sms", preferences.sms_enabled)] if enabled]
```

### Testing Deliveries

```python
def test_publication_email(mailoutbox, post, recipient):
    published_message(post=post, recipient=recipient).send(fail_silently=False)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [recipient.email]
    assert post.title in mailoutbox[0].subject
```

## Without explicit delivery

### Service-Based Approach

```python
def notify_publication(*, post, preferences, adapters):
    for channel in publication_channels(post=post, preferences=preferences):
        adapters[channel].send(post=post)
# Specify per-channel durable outcomes before retrying this orchestration.
```

## Triggering Notifications from State Machines

When notifications are tied to state transitions, standalone workflows are an ideal place to trigger them via `after_transition` callbacks. This keeps models free of notification logic while centralizing state-related side effects.

```python
@transaction.atomic
def finish_provisioning(*, cable):
    cable.mark_created()
    cable.save(update_fields=["status"])
    DeliveryIntent.objects.create(cable=cable, event="provisioned")
```

## Anti-Patterns

### Notifications in Models

```python
# Notifications belong in the operation; the domain mutation stays focused.
post.publish(at=timezone.now())
post.save(update_fields=["published_at"])
transaction.on_commit(partial(notify_publication, post_id=post.pk))
```

### Mailer Knows Too Much

```python
message = published_message(post=post, recipient=recipient)
# The formatter does not decide roles, choose recipients or send other messages.
message.send(fail_silently=False)
```

### Inline Notification Logic

```python
def publish(request, post_id):
    publish_post_for_actor(post_id=post_id, actor=request.user)
    return redirect_303("posts")
```

## Delivery Patterns

### Batch Notifications

```python
def request_daily_digests(*, since):
    for user in User.objects.filter(notificationpreferences__digest_enabled=True).iterator():
        posts = user.unread_posts.filter(created_at__gte=since)
        if posts.exists():
            request_digest(user_id=user.pk, since=since)
# request_digest owns an idempotency key for user + reporting period.
```

### Notification Objects

```python
class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    kind = models.CharField(max_length=40)
    read_at = models.DateTimeField(null=True)

    def mark_read(self, *, at):
        self.read_at = at
        self.save(update_fields=["read_at"])
```
