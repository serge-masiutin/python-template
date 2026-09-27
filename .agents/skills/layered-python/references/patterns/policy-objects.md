# Policy Objects

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Authorization in Views
- Roles and Permissions
- Scoping-Based Authorization
- N+1 Authorization Problem
- Testing
- Anti-Patterns
- Related Mechanisms

## Summary

Policy objects encapsulate authorization rules, determining whether a user can perform specific actions on resources. They belong to the application layer, sitting between presentation (enforcement) and domain (entities).

## When to Use

- Authorization logic beyond simple ownership checks
- Role-based or attribute-based access control
- Reusable authorization rules across controllers
- Testing authorization independently from controllers

## When NOT to Use

- Simple ownership checks (`post.user_id == current_user.id`)
- Authentication (who is this user?)

## Key Principles

- **Separate from authentication** — authentication identifies, authorization permits
- **Keep in services layer** — policies are application-layer abstractions
- **Never leak to domain** — models live in already-authorized context
- **Predicate interface** — methods return true/false
- **Convention-based lookup** — `PostPolicy` for `Post` model

## Implementation

### Plain Python Policy

```python
@dataclass(frozen=True)
class BookPolicy:
    actor: User
    book: Book

    def can_view(self):
        return True

    def can_delete(self):
        return self.actor.has_perm("library.manage_all_books") or (
            self.actor.has_perm("library.manage_books") and self.book.department_id == self.actor.department_id
        )
```

### Usage in Controller

```python
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if not BookPolicy(request.user, book).can_delete():
        raise PermissionDenied
    book.delete()
    return redirect_303("books")
```

### With Explicit Django Policies

```python
# Use Django permissions for capabilities; add explicit resource policy rules.
def can_manage_book(*, actor, book):
    return actor.has_perm("library.manage_all_books") or (
        actor.has_perm("library.manage_books") and book.department_id == actor.department_id
    )
```

### Controller with `authorize!`

```python
book = get_object_or_404(Book, pk=book_id)
if not can_manage_book(actor=request.user, book=book):
    raise PermissionDenied
book.delete()
```

## Authorization in Views

```tsx
{books.map(book => <li key={book.id}>
  {book.name}
  {book.canDelete && <DeleteBook bookId={book.id} />}
</li>)}
```

## Roles and Permissions

### Role-Based (RBAC)

```python
# Define permissions in Meta.permissions and assign them to Groups via a
# data migration or management command. is_staff grants admin-site entry only.
user.has_perm("library.manage_books")
user.has_perm("library.manage_librarians")
```

### Attribute-Based (ABAC)

Any attribute can influence access:

```python
def can_delete_book(*, actor, book):
    if actor.has_perm("library.manage_all_books"):
        return True
    if not actor.has_perm("library.manage_books"):
        return False
    return book.department_id == actor.department_id
```

## Scoping-Based Authorization

Combine data loading with authorization:

```python
def destroyable_books(*, actor):
    if actor.has_perm("library.manage_all_books"):
        return Book.objects.all()
    if actor.has_perm("library.manage_books"):
        return Book.objects.filter(department_id=actor.department_id)
    return Book.objects.none()

book = get_object_or_404(destroyable_books(actor=request.user), pk=book_id)
book.delete()
```

## N+1 Authorization Problem

```python
# Avoid a database query in each policy check. Resolve shared capabilities once.
can_publish = actor.has_perm("posts.publish_post")
props = [{"id": str(post.pk), "canPublish": can_publish and post.author_id == actor.pk} for post in posts]
```

**Solutions:**
- Preload data needed by policy rules
- Cache authorization results
- Use scoping-based authorization

## Testing

Test policy rules separately from enforcement:

```python
@pytest.mark.django_db
def test_policy_rejects_other_department(librarian, book):
    assert BookPolicy(librarian, book).can_delete()
    book.department_id = another_department.pk
    assert not BookPolicy(librarian, book).can_delete()

@pytest.mark.django_db
def test_delete_enforces_scope(client, other_user, book):
    client.force_login(other_user)
    response = client.post(f"/books/{book.pk}/delete/")
    assert response.status_code in {403, 404}
    assert Book.objects.filter(pk=book.pk).exists()
```

## Anti-Patterns

### Authorization in Models

```python
# Keep role and resource authorization separate from a book's domain state.
policy = BookPolicy(actor, book)
if not policy.can_delete():
    raise PermissionDenied
```

### Mixed Enforcement Layers

```python
# The HTTP boundary enforces this operation's policy before deleting.
# A worker or CLI invoking it needs its own explicit execution authority.
if not BookPolicy(request.user, book).can_delete():
    raise PermissionDenied
book.delete()
```

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| explicit Django policies | Authorization framework with policies |
