# Explicit Python JSON Shapes

Adaptation of explicit DTOs's entity allowlists, associations, conditional fields, naming,
consumer types, performance and testing guidance. Use the installed Django encoder
and explicit dictionaries; a serializer framework is not needed for every page.

## Installation and Basic Usage

```python
def user_summary(user):
    return {"id": str(user.pk), "email": user.email,
            "fullName": user.get_full_name()}

response = JsonResponse({"user": user_summary(user)})
```

The application replaces inertia-django's model-aware encoder with
`DjangoJSONEncoder`. Passing an ORM model or QuerySet directly must fail; all public
fields are chosen before rendering.

## Associations

```python
posts = authorized_posts(actor).select_related("author")[:50]
props = {"posts": [{"id": str(post.pk), "title": post.title,
                    "author": user_summary(post.author)} for post in posts]}
```

The query layer preloads relations. A serializer does not authorize, query, mutate
or read global request state.

## Conditional and Computed Attributes

Pass already established access context explicitly. Separate admin and public
contracts when their shapes differ substantially. Pure display calculations are
allowed; use model methods for domain calculations.

## Root Key, Base Serializer and Key Transformation

Choose a stable response envelope per consumer. Reuse named functions where a shape
actually repeats. No base serializer or inferred class lookup is required. Spell
frontend field names explicitly instead of applying a global case transformation
that can silently change nested user data.

## TypeScript Generation

Keep Python and TypeScript public shapes together in a change. A `TypedDict` can
help static checks but does not validate network input. Add code generation only
from a real schema and retain generator, inputs and reproducible output.

## Performance Tips

Bound collections, use `select_related` for to-one and `prefetch_related` for to-many
relations, and measure query growth. `only()` may cause deferred-field N+1 if the
serializer reads omitted fields. Decimal money and large IDs need deliberate string
representation; timestamps need timezone and precision contracts.

## Testing

Assert exact keys, nullability and representation, not just inclusion. Test both
public and privileged views and query counts for collections. Never expose password
hashes, session tokens, raw provider output or unrestricted `model_to_dict` results.
