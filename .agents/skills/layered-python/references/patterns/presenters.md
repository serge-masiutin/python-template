# Presenters

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- With Keynote (Library)
- Anti-Patterns
- Testing
- Related Mechanisms

## Summary

Presenters encapsulate representation logic for views. They bridge models and the view layer, extracting UI-specific formatting, CSS classes, and display logic from domain objects.

## When to Use

- View-specific formatting (dates, names, statuses)
- CSS class generation based on state
- Combining data from multiple models for display
- Logic that's only needed in views

## When NOT to Use

- Domain logic (belongs in models)
- Data transformation for APIs (use serializers)
- Simple attribute access

## Key Principles

- **Presentation layer** — never leak presenters to lower layers
- **Explicit interface (closed)** vs **delegation (open)** — choose based on isolation needs
- **One presenter per view context** — avoid god presenters
- **Test presenters independently** — no full request cycle needed

## Implementation

### Closed Presenter (Explicit Interface)

Best for strict isolation:

```python
@dataclass(frozen=True)
class UserPresenter:
    user: User

    def short_name(self):
        parts = self.user.get_full_name().split()
        return "".join(p[0] + "." for p in parts[:-1]) + parts[-1] if parts else self.user.username

    def props(self):
        return {"id": str(self.user.pk), "shortName": self.short_name(),
                "status": self.user.status, "memberSince": date_format(self.user.date_joined, "F Y")}
```

### Open Presenter (Decorator)

Delegates all methods, adds presentation logic:

```python
# Explicit composition keeps the presentation API small; avoid __getattr__ delegation.
summary = UserPresenter(user).props()
```

### Multi-Model Presenter

For composite UI elements:

```python
@dataclass(frozen=True)
class BookPresenter:
    book: Book
    reading: BookReading

    def props(self):
        return {"title": self.book.title, "read": self.reading.read_at is not None,
                "score": self.reading.score}
```

### Presenter Helper

```python
# Select the presenter explicitly, without naming conventions or reflection.
return_value = UserPresenter(user).props()
```

### Usage in Views

```tsx
<span><StatusBadge status={user.status} />{user.shortName}</span>
<small>Member since {user.memberSince}</small>
```

## With Keynote (Library)

```python
# Keep markup in React and deterministic display calculations in the presenter.
props = {**UserPresenter(user).props(), "avatarUrl": user.avatar_url}
```

## Anti-Patterns

### Representation Logic in Models

```python
# Bad: domain models naming CSS classes couple them to the UI.
class User(models.Model):
    def status_badge_class(self):
        return "badge-success" if self.is_active else "badge-muted"
# Prefer a semantic status prop and React's StatusBadge variant.
```

### Leaking Decorators

```python
# Pass domain objects to operations, then present their results at the HTTP boundary.
user = update_profile(actor=actor, fields=fields)
props = UserPresenter(user).props()
```

### Global Helpers with Prefixes

```python
presenter = UserPresenter(user)
short_name = presenter.short_name()
props = presenter.props()
```

## Testing

```python
def test_presenter_abbreviates_name():
    user = User(username="john", first_name="John Michael", last_name="Doe")
    assert UserPresenter(user).short_name() == "J.M.Doe"
```

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| keynote | Presenters with caching and view helpers |
