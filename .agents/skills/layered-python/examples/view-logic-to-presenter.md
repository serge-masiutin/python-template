# Extract View Logic to Presenter

Move complex view computations out of templates into a presenter wrapping the model.

## Before

```tsx
function Profile({ user }: { user: ProfileProps }) {
  const names = user.name.trim().split(/\s+/);
  return <section>
    <span className={user.status === "active" ? "badge-success" : "badge-warning"}>{user.status}</span>
    <h1>{names.slice(0, -1).map(name => name[0] + ".").join("") + names.at(-1)}</h1>
    <p>Member since {user.memberSince}</p>
  </section>;
}
```

## After

```python
from dataclasses import dataclass
from django.utils.formats import date_format


@dataclass(frozen=True)
class UserPresenter:
    user: User

    def props(self):
        names = self.user.get_full_name().split()
        short_name = "".join(name[0] + "." for name in names[:-1]) + names[-1] if names else self.user.username
        return {
            "status": self.user.status,
            "shortName": short_name,
            "memberSince": date_format(self.user.date_joined, "F Y"),
        }
```

```tsx
function Profile({ user }: { user: PresentedProfile }) {
  return <section>
    <StatusBadge status={user.status} />
    <h1>{user.shortName}</h1>
    <p>Member since {user.memberSince}</p>
  </section>;
}
```
