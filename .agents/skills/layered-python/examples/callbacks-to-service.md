# Extract Callbacks to Service

Move multi-step user-creation side effects out of `post_save receiver` callbacks into an explicit service.

## Before

```python
# Bad: saving a user implicitly performs the whole registration workflow.
@receiver(post_save, sender=User)
def register_side_effects(sender, instance, created, **kwargs):
    if created:
        send_welcome_email(instance.pk)
        Workspace.objects.create(owner=instance, name="My Workspace")
        notify_admin(instance.pk)
        track_signup(instance.pk)
```

## After

```python
from django.db import transaction
from functools import partial


@transaction.atomic
def register_user(*, username, email, password):
    user = User.objects.create_user(username=username, email=email, password=password)
    Workspace.objects.create(owner=user, name="My Workspace")
    transaction.on_commit(partial(send_welcome_email, user.pk))
    transaction.on_commit(partial(notify_admin, user.pk))
    transaction.on_commit(partial(track_signup, user.pk))
    return user


@require_POST
def register(request):
    form = RegistrationForm(request.POST)
    if not form.is_valid():
        return invalid_form(request, form, destination="register")
    user = register_user(**form.cleaned_data)
    return redirect_303("user-detail", user_id=user.pk)
```

`on_commit` prevents sending before commit; it is not durable delivery. If a
notification must survive a process crash, insert a delivery-intent record in the
same transaction and let a worker claim it. Do not retry an uncertain send blindly.
