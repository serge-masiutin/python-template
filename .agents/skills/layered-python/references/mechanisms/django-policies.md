# Django Permissions and Explicit Policies

Adaptation of the Action Policy reference: preserve rule ownership, scoped queries,
explicit actor context, composition and enforcement tests. Django does not provide
Action Policy's rule inference, aliases, reasons or object scopes.

## Installation

Use the installed `django.contrib.auth` permissions and groups. Do not install an
object-permissions framework until a concrete policy requires it. Django's default
backend does not implement arbitrary object permissions through `has_perm(..., obj)`.

## Basic Usage

### Define Policy

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PostPolicy:
    actor: User
    post: Post

    def can_update(self):
        return self.actor.is_superuser or self.post.author_id == self.actor.pk
```

### Controller Integration

```python
post = get_object_or_404(Post, pk=post_id)
if not PostPolicy(request.user, post).can_update():
    raise PermissionDenied
```

### View Integration

Send an explicit `canUpdate` boolean to React for affordances. The mutation view
must still enforce the same decision. Django `is_staff` means admin-site access,
not unrestricted business authority.

## Scoping

```python
def visible_posts(*, actor):
    if actor.has_perm("posts.view_all_posts"):
        return Post.objects.all()
    return Post.objects.filter(author=actor)
```

Apply the scope before lookup, pagination and serialization, including deferred
requests. Decide deliberately whether a denied lookup yields 403 or hides existence
with 404. Permission predicates must not enqueue, write, or call external services.

## Rule Aliases and Minimal CRUD Rules

Use small named methods or functions; share a rule by calling it explicitly.
Keep create/read/update/delete rules minimal. Add a custom rule for a real domain
transition; when confirmation, creation and reversal form a separate resource,
consider its own policy rather than accumulating unrelated methods.

## Reason Tracking and Policy Composition

A denial reason can be a small enum returned by a pure decision function. Do not
leak sensitive records or internal details in a response. Compose focused policies
with explicit actor and record arguments, not request globals.

## Pre-Checks and Authorization Context

Authentication belongs at the entry point. Pass tenant and actor separately when
both are required. Mark optional actor context explicitly; do not let an absent
actor accidentally skip authorization. Workers and commands establish their own
execution authority instead of inheriting a browser request.

## Error Handling and Gotchas

Raise `PermissionDenied` for forbidden actions. Narrow missing-record handling to
`get_object_or_404` at the HTTP boundary. Do not catch all exceptions as denials.
Permission caching is per User instance in Django; re-read the user when permission
changes must be reflected immediately. Measure query growth in collection policies.

## Testing

Test allowed and denied policy cases, different owners/tenants and inactive users.
Integration tests must prove an unauthorized mutation changes no records. A UI test
that hides a button does not prove enforcement. Use Django tests/pytest, not an
assertion that merely spies on the policy method being called.
