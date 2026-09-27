# Authorization as Props

Pass permissions as props — the frontend decides what to **show**, the server
decides what to **allow**. Never check permissions client-side only.

## Controller Pattern

```python
@login_required
def show(request, user_id):
    user = get_object_or_404(users_visible_to(request.user), pk=user_id)
    return render(request, "Users/Show", props={
        "user": user_summary(user),
        "can": {"edit": can_edit(actor=request.user, user=user),
                "delete": can_delete(actor=request.user, user=user)},
    })
# Repeat authorization on every mutation; these booleans only control presentation.
```

## Frontend Pattern

```tsx
export default function Show({ user, can }: Props) {
  return (
    <>
      <h1>{user.name}</h1>
      {can.edit && <Link href={`/users/${user.id}/edit`}>Edit</Link>}
      {can.delete && <DeleteButton userId={user.id} />}
    </>
  )
}
```

## Key Rules

- **Always enforce server-side** — `can` props control UI visibility, not access. The `update`/`destroy` actions must independently authorize.
- **Per-record, not global** — pass `can` per resource, not a blanket `isAdmin` flag. A user may edit their own profile but not others.
- **Explicit Django policies** — use model permissions for model-wide access and owner/tenant-scoped queries for records. Add object policies as explicit functions; Django core does not implement object permissions merely because an object is passed to has_perm.
