# Extract Authorization to Policy

Replace duplicated controller-side authorization checks with a policy object.

## Before

```python
# Before: duplicated access decisions in HTTP views.
def update_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not (request.user.is_superuser or post.author_id == request.user.pk):
        raise PermissionDenied
    form = PostForm(request.POST, instance=post)
    if form.is_valid():
        form.save()
        return redirect_303("post-detail", post_id=post.pk)
    return invalid_form(request, form, destination="post-edit")


def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not request.user.is_superuser:
        raise PermissionDenied
    post.delete()
    return redirect_303("posts")
```

## After

```python
from dataclasses import dataclass
from django.core.exceptions import PermissionDenied


@dataclass(frozen=True)
class PostPolicy:
    actor: User
    post: Post

    def can_update(self):
        return self.actor.is_superuser or self.post.author_id == self.actor.pk

    def can_delete(self):
        return self.actor.is_superuser


def update_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not PostPolicy(request.user, post).can_update():
        raise PermissionDenied
    form = PostForm(request.POST, instance=post)
    if form.is_valid():
        form.save()
        return redirect_303("post-detail", post_id=post.pk)
    return invalid_form(request, form, destination="post-edit")


def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not PostPolicy(request.user, post).can_delete():
        raise PermissionDenied
    post.delete()
    return redirect_303("posts")
```
