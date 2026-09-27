# Callback Anti-Patterns

Misuses of Django ORM callbacks that signal a layering problem.

## Contents

- Operation Callbacks
- Skip Callback Anti-Pattern
- Callback Control Flags

## Operation Callbacks

**Problem:** Business process steps disguised as callbacks.

```python
@receiver(post_save, sender=User)
def hidden_signup(sender, instance, created, **kwargs):
    if created:
        create_initial_project(instance)
        send_welcome_email(instance.pk)
        sync_crm(instance.pk)
        track_signup(instance.pk)
```

**Fix:** Extract to controller, service, or events.

```python
@transaction.atomic
def register_user(*, username, password):
    user = User.objects.create_user(username=username, password=password)
    create_initial_project(user)
    transaction.on_commit(partial(send_welcome_email, user.pk))
    transaction.on_commit(partial(sync_crm, user.pk))
    return user
```

## Skip Callback Anti-Pattern

**Problem:** `skip_before_action` creates hidden dependencies.

```python
class DashboardView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        # Bad: bypassing a superclass silently removes its access contract.
        return View.dispatch(self, request, *args, **kwargs)
```

**Fix:** Use explicit inheritance or composition.

```python
@login_required
def dashboard(request):
    return render(request, "Dashboard")


def public_home(request):
    return render(request, "PublicHome")
```

## Callback Control Flags

**Problem:** Virtual attributes to skip callbacks.

```python
@receiver(post_save, sender=User)
def welcome(sender, instance, created, **kwargs):
    if created and not instance.skip_welcome_email:
        send_welcome_email(instance.pk)

user.skip_welcome_email = True
user.save()
```

**Fix:** Extract callbacks, call explicitly when needed.

```python
@transaction.atomic
def register_user(*, username, password, send_welcome=True):
    user = User.objects.create_user(username=username, password=password)
    if send_welcome:
        transaction.on_commit(partial(send_welcome_email, user.pk))
    return user
```
