# Authorization

## Contents

- Summary
- Layer Placement
- Key Principles
- Implementation with Explicit Django Policies
- Error Handling
- Anti-Patterns
- Testing
- N+1 Authorization

## Summary

Authorization determines what authenticated users can do. It belongs in the application layer as policy objects, enforced at presentation layer entry points, never leaking into domain models.

## Layer Placement

```
┌─────────────────────────────────────────┐
│ Presentation Layer                      │
│  └─ Enforcement (authorize! calls)      │
├─────────────────────────────────────────┤
│ Application Layer                       │
│  └─ Policy Objects (rules live here)    │
├─────────────────────────────────────────┤
│ Domain Layer                            │
│  └─ Models operate in authorized context│
└─────────────────────────────────────────┘
```

## Key Principles

- **Single enforcement point** — authorize in controllers, nowhere else
- **Policies are application layer** — bridge between presentation and domain
- **Models are agnostic** — domain doesn't know about permissions
- **Scoping over checking** — load only accessible records when possible
- **Minimal rules** — `show?` for visibility, `manage?` for modifications
- **Composition over complexity** — delegate to other policies via `allowed_to?`

## Implementation with Explicit Django Policies

### Basic Policy

```python
@dataclass(frozen=True)
class PostPolicy:
    actor: User
    post: Post

    def can_view(self):
        return self.post.is_public or self.can_update()

    def can_update(self):
        return self.actor.is_superuser or self.post.author_id == self.actor.pk

    def can_delete(self):
        return self.actor.is_superuser
```

### Rule Design

Keep rules minimal and consistent:

| Rule | Purpose |
|------|---------|
| `show?` | Visibility — who can see this resource |
| `manage?` | Management — fallback for update?, destroy?, etc. |
| `create?` | Creation — often delegates to parent's manage? |
| `index?` | Listing — often same as show? or delegates to parent |

**Custom rules** are appropriate for domain operations (`transfer?`, `cancel?`) and parent policy groupings (`manage_billing?`). If a custom rule maps to a full controller with its own views, consider a dedicated resource instead.

### Controller Enforcement

```python
def update(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not PostPolicy(request.user, post).can_update():
        raise PermissionDenied
    form = PostForm(request.POST, instance=post)
    if not form.is_valid():
        return invalid_form(request, form, destination="post-edit")
    form.save()
    return redirect_303("post-detail", post_id=post.pk)
```

### Scoping-Based Authorization

Prefer loading only accessible records:

```python
def visible_posts(*, actor):
    if actor.is_superuser:
        return Post.objects.all()
    return Post.objects.filter(Q(author=actor) | Q(is_public=True))


def destroyable_posts(*, actor):
    return Post.objects.all() if actor.is_superuser else Post.objects.none()

post = get_object_or_404(destroyable_posts(actor=request.user), pk=post_id)
```

### View Authorization

```tsx
{posts.map(post => <article key={post.id}>
  <h2>{post.title}</h2>
  {post.canUpdate && <Link href={post.editUrl}>Edit</Link>}
  {post.canDelete && <DeletePost postId={post.id} />}
</article>)}
```

### Role-Based Access Control (RBAC)

```python
# Django Groups collect model permissions. Object access adds explicit rules.
def can_update(*, actor, post):
    return actor.has_perm("posts.change_post") and (
        post.author_id == actor.pk or actor.has_perm("posts.manage_all_posts")
    )
```

### Attribute-Based Access Control (ABAC)

```python
@dataclass(frozen=True)
class DocumentPolicy:
    actor: User
    document: Document

    def can_view(self):
        return (self.document.is_public or self.actor.department_id == self.document.department_id
                or self.document.shared_with(self.actor))

    def can_edit(self):
        return not self.document.is_locked and (
            self.document.owner_id == self.actor.pk or self.actor.manages(self.document.owner)
        )
```

## Error Handling

Return 404 for visibility failures (don't leak resource existence), 403 for permission failures:

```python
document = get_object_or_404(visible_documents(request.user), pk=document_id)
if not DocumentPolicy(request.user, document).can_edit():
    raise PermissionDenied
# Scoped lookup yields 404; visible but forbidden mutation yields 403.
```

## Anti-Patterns

### Authorization in Models

```python
policy = PostPolicy(actor, post)
allowed = policy.can_update()  # Pure policy decision, separate from domain state.
```

### Multiple Enforcement Points

```python
# Enforce once at the boundary that all callers must cross.
publish_post(post_id=post_id, actor=request.user)
# That operation enforces publish access; the HTTP view does not duplicate the rule.
```

### Implicit Authorization

```python
# Ownership is a valid explicit scope when it is the complete access rule.
notes = Note.objects.filter(owner=request.user)
# Extract a named scope when rules grow beyond this direct relationship.
```

## Testing

### Policy Unit Tests

```python
def test_policy_allows_owner_and_denies_others(owner, stranger, post):
    assert PostPolicy(owner, post).can_update()
    assert not PostPolicy(stranger, post).can_update()
```

### Controller Authorization Tests

```python
@pytest.mark.django_db
def test_update_does_not_modify_forbidden_post(client, stranger, post):
    client.force_login(stranger)
    before = post.title
    response = client.post(f"/posts/{post.pk}/", {"title": "New"})
    assert response.status_code == 403
    post.refresh_from_db()
    assert post.title == before
```

## N+1 Authorization

```python
# Bad when shared_with() executes one SQL query for every record.
props = [{"id": str(p.pk), "canView": p.shared_with(actor)} for p in posts]
```

Solutions:

1. **Preload required data** for policy checks
2. **Cache authorization** results
3. **Use scoping** instead of per-record checks

```python
posts = list(visible_posts(actor=actor).select_related("author")[:50])
editable_ids = set(editable_posts(actor=actor).filter(pk__in=[p.pk for p in posts]).values_list("pk", flat=True))
props = [{"id": str(p.pk), "canUpdate": p.pk in editable_ids} for p in posts]
```
