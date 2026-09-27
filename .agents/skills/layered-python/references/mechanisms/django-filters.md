# Django Forms for Request Filters

Adaptation of Rubanok's input mapping, matching, sorting, pagination and failure
strategy. Django forms validate request syntax; query functions compose an already
authorized QuerySet.

## Installation and Basic Usage

```python
from django import forms

class ProjectFilters(forms.Form):
    status = forms.ChoiceField(choices=[("draft", "Draft"), ("published", "Published")], required=False)
    q = forms.CharField(max_length=100, required=False)
    sort = forms.ChoiceField(choices=[("name", "Name"), ("-created_at", "Newest")], required=False)
    page = forms.IntegerField(min_value=1, required=False)

filters = ProjectFilters(request.GET)
if not filters.is_valid():
    raise BadRequest("Invalid filters")
```

## Param Mapping and Matching

Use `cleaned_data` after validation. Apply only named fields; do not forward request
keys into `filter(**...)` or `order_by`. Normal query composition stays in the model's
QuerySet or a domain-named query function.

```python
values = filters.cleaned_data
projects = authorized_projects(request.user)
if values["status"]:
    projects = projects.filter(status=values["status"])
if values["q"]:
    projects = projects.filter(name__icontains=values["q"])
projects = projects.order_by(values["sort"] or "-created_at", "pk")
```

## Failure Strategy for Invalid Params

Invalid choices produce a 400/error response; do not silently discard them or return
an empty result. Absence of an explicitly optional filter is a separate valid case.

## Nested Params

Define a schema for nested JSON at its decoder boundary. Django QueryDict does not
turn `filter[status]` into a nested Python object automatically. Either use flat
query keys or parse the exact documented nested representation.

## Sorting and Pagination

Allowlist sort fields/directions and add a stable tiebreaker. Bound page size and
choose page/cursor semantics from the real feature. Validate page numbers before
calling the paginator; do not silently map an invalid page to the last page.

## With Form Object

A form handles input conversion and validation; a query handles retrieval. Reuse
those boundaries rather than generating an application-wide filter base class.

## Testing

Test malformed values, unknown choices, tenant scope, search escaping, pagination
limits and stable ordering. Include repeated parameters when the contract requires
one value per key. ORM parameter binding protects values, not arbitrary field names.
