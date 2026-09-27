# Filter Objects

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Filter vs Query Object
- Anti-Patterns
- Security Considerations
- Related Mechanisms

## Summary

Filter objects transform datasets based on user-provided parameters. They belong to the presentation layer, consuming request parameters and applying transformations to domain collections.

## When to Use

- Request parameter filtering/transformation
- Search interfaces with multiple optional filters
- Sorting and pagination logic
- Parameter sanitization before domain layer

## When NOT to Use

- Domain-specific queries (use query objects)
- Form submissions (use form objects)

## Key Principles

- **Presentation layer** — consumes user input, not domain logic
- **One filter per interface** — avoid universal filter objects
- **Can use query objects internally** — filters orchestrate, queries implement
- **Declarative over imperative** — use DSL for common patterns

## Implementation

### With Rubanok (Recommended)

```python
class ProjectsFilter(forms.Form):
    status = forms.ChoiceField(choices=[("draft", "Draft"), ("published", "Published")], required=False)
    time = forms.ChoiceField(choices=[("future", "Future"), ("past", "Past")], required=False)
    sort = forms.ChoiceField(choices=[("name", "Name"), ("-started_at", "Newest")], required=False)
    q = forms.CharField(max_length=100, required=False)

    def apply(self, projects):
        filters = self.cleaned_data
        if filters["status"]:
            projects = projects.filter(status=filters["status"])
        if filters["time"] == "future":
            projects = projects.filter(started_at__gt=timezone.now())
        elif filters["time"] == "past":
            projects = projects.filter(started_at__lte=timezone.now())
        if filters["q"]:
            projects = projects.filter(name__icontains=filters["q"])
        return projects.order_by(filters["sort"] or "-started_at", "pk")
```

### Usage

```python
filters = ProjectsFilter(request.GET)
if not filters.is_valid():
    raise BadRequest("Invalid project filters")
projects = filters.apply(authorized_projects(request.user))
```

### Plain Python Implementation

```python
def filter_projects(projects, *, status, query, order):
    # Inputs already passed ProjectsFilter; optional blank values are a form contract.
    if status:
        projects = projects.filter(status=status)
    if query:
        projects = projects.filter(name__icontains=query)
    return projects.order_by(order, "pk")
```

## Filter vs Query Object

| Aspect | Filter Object | Query Object |
|--------|---------------|--------------|
| Layer | Presentation | Domain |
| Input | Request params | Domain values |
| Purpose | UI filtering | Reusable queries |
| Location | `app/filters/` | `<feature>/queries/` |

```python
class PostsFilter(forms.Form):
    trending = forms.BooleanField(required=False)

    def apply(self, posts):
        return trending_posts(posts, min_views=100, since=yesterday) if self.cleaned_data["trending"] else posts
```

## Anti-Patterns

### Universal Filter Object

```python
# Bad: a generic filter accepts arbitrary model field names from a request.
results = model.objects.filter(**request.GET.dict())
```

**Fix:** Create interface-specific filters:

```python
class AdminUsersFilter(forms.Form):
    department = forms.CharField(max_length=100, required=False)

class PublicUsersFilter(forms.Form):
    display_name = forms.CharField(max_length=100, required=False)
```

### Filtering in Controller

```python
def index(request):
    filters = ProjectsFilter(request.GET)
    if not filters.is_valid():
        raise BadRequest("Invalid filters")
    projects = filters.apply(authorized_projects(request.user))
    return render(request, "Projects", props={"projects": [project_summary(p) for p in projects[:50]]})
```

## Security Considerations

Always whitelist allowed values:

```python
class ProjectsFilter(forms.Form):
    status = forms.ChoiceField(choices=[("draft", "Draft"), ("published", "Published")])
# Invalid values produce form errors; never silently ignore them.
```

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| validated QuerySet filters | Parameter-based transformation pipelines |
| Django Form + QuerySet | Explicitly apply validated filters |
| filterameter | Declarative filter DSL |
