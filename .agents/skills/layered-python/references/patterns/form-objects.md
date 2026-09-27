# Form Objects

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Usage in Controllers
- Wizard Forms (Multi-Step)
- Anti-Patterns
- Related Mechanisms

## Summary

Form objects handle specific user interactions involving data submission. They belong to the presentation layer and are useful when the form doesn't map 1:1 to a model — creating multiple records, updating virtual attributes, or handling complex validation contexts.

## When to Use

- Multi-model forms (creating/updating multiple records)
- Model-less forms (feedback, search, settings)
- Context-specific validations (publish vs draft)
- Complex form logic that doesn't belong in models

## When NOT to Use

- For simple single-model CRUD use ModelForm with an explicit fields allowlist
- Duplicating model validations

## Key Principles

- **Presentation layer abstraction** — handles UI concerns, not domain logic
- **Use when N ≠ 1** — forms that create/update zero, multiple, or virtual resources
- **Build on Django forms** — field validation, clean methods and typed cleaned_data
- **Explicit operations for side effects** — transaction.atomic groups writes; on_commit runs after a successful commit but does not guarantee durable delivery
- **Don't duplicate validations** — delegate to models and merge errors

## Implementation

### Base Class

```python
# Django already provides forms.Form and forms.ModelForm.
# Do not reproduce an forms.Form callback framework.
class InvitationForm(forms.Form):
    email = forms.EmailField()
    send_copy = forms.BooleanField(required=False)
```

### Context-Specific Form

```python
@transaction.atomic
def invite_user(*, email, send_copy, sender):
    invitation = Invitation.objects.create(email=email, sender=sender)
    transaction.on_commit(partial(deliver_invitation, invitation.pk))
    if send_copy:
        transaction.on_commit(partial(deliver_invitation_copy, invitation.pk, sender.pk))
    return invitation
```

### Multi-Model Form

```python
class RegistrationForm(forms.ModelForm):
    project_name = forms.CharField(max_length=100, required=False)
    should_create_project = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("should_create_project") and not cleaned.get("project_name"):
            self.add_error("project_name", "Enter a project name")
        return cleaned


@transaction.atomic
def register_with_project(*, username, email, project_name, should_create_project):
    user = User.objects.create_user(username=username, email=email)
    if should_create_project:
        Project.objects.create(owner=user, name=project_name)
    return user
```

### Model-less Form

```python
class FeedbackForm(forms.Form):
    message = forms.CharField(min_length=10, max_length=2000)
    email = forms.EmailField()
    category = forms.ChoiceField(choices=[("bug", "Bug"), ("idea", "Idea")])

# Once valid, pass cleaned_data to an explicit delivery operation.
```

## Usage in Controllers

```python
def create_invitation(request):
    form = InvitationForm(request.POST)
    if not form.is_valid():
        return invalid_form(request, form, destination="invitation-new")
    invite_user(sender=request.user, **form.cleaned_data)
    messages.success(request, "Invitation sent")
    return redirect_303("invitations")
```

## Wizard Forms (Multi-Step)

Use state machines for complex multi-step forms:

```python
class ProfileStep(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()

class PreferencesStep(forms.Form):
    theme = forms.ChoiceField(choices=[("light", "Light"), ("dark", "Dark")])

# Persist authorized draft state on the server. Validate each step, then validate
# the combined draft on confirmation before one atomic registration operation.
form = ProfileStep(request.POST)
if form.is_valid():
    save_onboarding_step(actor=request.user, step="profile", fields=form.cleaned_data)
```

## Anti-Patterns

### Duplicating Model Validations

```python
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]
# ModelForm invokes model validation for included fields. Database uniqueness
# still resolves races; plain model.save() never invokes full_clean().
```

### UI Logic in Model Callbacks

```python
@transaction.atomic
def register_user(*, username, password):
    user = User.objects.create_user(username=username, password=password)
    transaction.on_commit(partial(send_welcome_email, user.pk))
    return user
```

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| django.db.transaction | atomic blocks and on_commit callbacks |
