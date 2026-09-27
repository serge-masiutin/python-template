# Extract Current from Model

Remove `ambient_actor` access from a domain model by moving authorization to a policy and ownership to the controller.

## Before

```python
# Bad: current_user is a ContextVar populated by HTTP middleware.
class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def can_edit(self):
        actor = current_user.get()
        return self.author_id == actor.pk or actor.is_superuser

    def save(self, *args, **kwargs):
        self.author = current_user.get()
        return super().save(*args, **kwargs)
```

## After

```python
class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


def can_edit_post(*, actor, post):
    return actor.is_superuser or post.author_id == actor.pk


@login_required
@require_POST
def create_post(request):
    form = PostForm(request.POST)
    if not form.is_valid():
        return invalid_form(request, form, destination="post-new")
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect_303("post-detail", post_id=post.pk)
```
