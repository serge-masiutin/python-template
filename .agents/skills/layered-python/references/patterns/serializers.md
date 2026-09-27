# Serializers

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Anti-Patterns
- Testing
- Related Mechanisms

## Summary

Serializers are specialized presenters for API responses. They form a dedicated abstraction layer between models and the external API contract, providing consistent JSON formatting and the ability to generate TypeScript types.

## When to Use

- API responses beyond simple JSON
- Multiple JSON formats for different contexts
- TypeScript frontend integration
- Versioned APIs

## When NOT to Use

- Simple `render json: @model`
- Internal data transformation

## Key Principles

- **Don't override `#as_json`** — couples model to API representation
- **Convention-based lookup** — `PostSerializer` for `Post` model
- **One serializer per context** — different serializers for list vs detail
- **Generate TypeScript types** — keep frontend in sync

## Implementation

### Plain Python Serializer

```python
def user_summary(user):
    return {"id": str(user.pk), "name": user.get_full_name()}


def post_summary(post):
    return {"id": str(post.pk), "title": post.title, "isDraft": post.is_draft,
            "user": user_summary(post.author)}
```

### explicit DTOs Serializer (Recommended)

```python
def post_detail(post, *, comments):
    return {**post_summary(post), "url": reverse("post-detail", kwargs={"post_id": post.pk}),
            "comments": [comment_summary(comment) for comment in comments]}
```

### Usage

```python
response = JsonResponse({"post": post_summary(post)})
collection_response = JsonResponse({"posts": [post_summary(post) for post in posts]})
```

### Convention-Based Lookup

```python
# Do not infer a serializer from an ORM class name; select its consumer contract.
response = JsonResponse({"post": post_detail(post, comments=comments)})
```

### Context-Specific Serializers

```python
def post_list_item(post):
    return {"id": str(post.pk), "title": post.title, "publishedAt": post.published_at}


def admin_post_detail(post):
    return {**post_list_item(post), "body": post.body, "status": post.status,
            "editUrl": reverse("admin:posts_post_change", args=[post.pk])}
```

### TypeScript Generation

```python
from typing import TypedDict

class PostSummary(TypedDict):
    id: str
    title: str
    isDraft: bool

# Pair this public shape with a TypeScript type and contract tests.
# TypedDict is static typing, not runtime validation.
```

Generated TypeScript:

```typescript
interface Post {
  id: number;
  title: string;
  is_draft: boolean;
  user: User;
}
```

## Anti-Patterns

### Overriding `#as_json` in Models

```python
# Bad: model_to_dict exposes fields according to persistence, not the consumer.
leaky_props = model_to_dict(post)
# Good: explicit allowlist.
public_props = post_summary(post)
```

### Multiple Formats Without Serializers

```python
def show(request, post_id):
    post = get_object_or_404(authorized_posts(request.user).select_related("author"), pk=post_id)
    return JsonResponse({"post": post_summary(post)})
```

## Testing

```python
def test_post_summary_has_only_public_fields(post):
    serialized = post_summary(post)
    assert set(serialized) == {"id", "title", "isDraft", "user"}
    assert serialized["id"] == str(post.pk)
    assert set(serialized["user"]) == {"id", "name"}
```

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| explicit DTOs | Fast JSON serialization with DSL |
| typelizer | Generate TypeScript from serializers |
