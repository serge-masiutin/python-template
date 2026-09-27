# Form Object for Complex Input

Replace a controller orchestrating multiple models with a form object that owns the registration workflow.

## Contents

- Before (fat controller)
- After (form object)

## Before

```python
# Bad: a transport entry point owns registration rules and persistence.
def register(request):
    user = User(username=request.POST["name"], email=request.POST["email"])
    user.set_password(request.POST["password"])
    if user.email.endswith("@company.com"):
        user.role = "employee"
        user.team = Team.objects.get(department=request.POST["department"])
    user.full_clean()
    user.save()
    Profile.objects.create(user=user, bio=request.POST["bio"])
    send_welcome_email(user.pk)
    return redirect_303("dashboard")
```

## After

```python
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from functools import partial


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(validators=[validate_password])
    name = forms.CharField(max_length=150)
    bio = forms.CharField(required=False)
    department = forms.CharField(max_length=100)
    avatar = forms.ImageField(required=False)


@transaction.atomic
def register_user(*, email, password, name, bio, department, avatar):
    employee = email.endswith("@company.com")
    team = Team.objects.get(department=department) if employee else None
    user = User(username=name, email=email, role="employee" if employee else "member", team=team)
    user.set_password(password)
    user.full_clean()
    user.save()
    Profile.objects.create(user=user, bio=bio, department=department, avatar=avatar)
    transaction.on_commit(partial(send_welcome_email, user.pk))
    return user


def register(request):
    form = RegistrationForm(request.POST, request.FILES)
    if not form.is_valid():
        return invalid_form(request, form, destination="register")
    user = register_user(**form.cleaned_data)
    return redirect_303("user-detail", user_id=user.pk)
```

The form owns input parsing and validation; the operation owns cross-model writes.
File storage does not roll back with SQL: define upload staging and cleanup before
using the avatar path in production. Email-domain classification is illustrative,
not proof of corporate membership. Privileged roles require verified authority.
