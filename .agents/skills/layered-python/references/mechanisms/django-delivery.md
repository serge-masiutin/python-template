# Explicit Delivery with Django

Adaptation of explicit delivery's orchestration, multiple-channel preferences and
testing guidance. Keep delivery decisions in the application layer and SMTP,
webhook or push implementations in infrastructure.

## Installation

Django includes an email interface; this starter does not install a durable queue,
Slack client or push SDK. Check the installed Django version's mailer configuration
before adding an adapter. Do not invent explicit delivery-style Python APIs.

## Basic Usage

### Define Delivery and Mailer

```python
from django.core.mail import EmailMessage

def welcome_message(*, recipient):
    return EmailMessage(subject="Welcome", body="Your workspace is ready.",
                        from_email="welcome@example.test", to=[recipient])

def send_welcome(*, recipient, connection):
    message = welcome_message(recipient=recipient)
    message.connection = connection
    return message.send(fail_silently=False)
```

The caller chooses the mail connection. Use the configured project's real sender;
the illustrative `example.test` address is not a production default.

### Trigger Delivery

Send explicitly after a successful commit. If loss is unacceptable, insert a
delivery-intent record in the same transaction and let a worker claim it. A commit
callback is not a durable queue, and successful SMTP acceptance is not inbox delivery.

## Multiple Channels

Represent each channel as a focused adapter. An application operation chooses
recipients, content and channels. Specify whether one channel failure blocks another;
record outcomes independently instead of swallowing exceptions to keep going.

## Conditional Delivery and User Preferences

Read current consent/preferences before sending. Separate mandatory transactional
messages from optional notifications. Template rendering must not perform database
queries or network calls. Do not infer permission to contact someone from a skill.

## Custom Delivery Lines

Webhook adapters validate destinations, bound timeouts, sign requests when required
and interpret non-success responses explicitly. Give externally repeated operations
idempotency keys where the provider supports them. A timeout may leave an unknown
outcome: reconcile before repeating a non-idempotent send.

## Testing

Test rendered recipients/content and the operation's delivery intent separately.
Use Django's in-memory email backend in tests and assert `mail.outbox`. Exercise
rollback, duplicate-job handling, preference changes and provider failure.

## Inline Mode (Development)

Use console or local mailbox delivery intentionally. Never point a development
preview or Storybook story at production SMTP. Immediate execution is not evidence
that the production queue, retries or crash recovery work.
