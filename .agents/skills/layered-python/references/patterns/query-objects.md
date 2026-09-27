# Query Objects

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Atomic vs Complex Scopes
- Using Arel
- Attaching Query Objects as Scopes
- Anti-Patterns
- Related Mechanisms

## Summary

Query objects encapsulate complex, context-specific database queries. They separate persistence concerns from domain models and provide reusable, testable query logic.

## When to Use

- Complex queries with multiple JOINs or subqueries
- Context-specific queries (not general model scopes)
- Queries reused across multiple controllers/services
- Queries that need parameterization

## When NOT to Use

- Simple queries (use model scopes)
- Single-condition filters (use atomic scopes)

## Key Principles

- **Atomic scopes in models** — simple, single-condition scopes stay in models
- **Complex queries in query objects** — multi-condition, context-specific queries
- **Use Arel for reusability** — avoid SQL string stitching
- **Explicit composition** — pass a scoped QuerySet; do not infer model classes from query names

## Implementation

### Base Class

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class BookmarkedAuthors:
    users: QuerySet
```

### Example Query Object

```python
def authors_with_bookmarks(users, *, start, end):
    author_ids = Post.objects.filter(
        created_at__gte=start, created_at__lt=end, bookmarks__isnull=False
    ).values("author_id").distinct()
    return users.filter(pk__in=Subquery(author_ids))
```

### Usage

```python
authors = authors_with_bookmarks(authorized_users(actor), start=start, end=end)
team_authors = authors_with_bookmarks(account.users.all(), start=start, end=end)
```

## Atomic vs Complex Scopes

### Atomic Scopes (Keep in Model)

Single condition, composable:

```python
class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(published_at__isnull=False)

    def recent(self, *, since):
        return self.filter(created_at__gte=since)

    def by_author(self, author):
        return self.filter(author=author)

posts = Post.objects.published().recent(since=last_week).by_author(actor)
```

### Complex Scopes (Extract to Query Object)

Multiple conditions, context-specific:

```python
def trending_posts(posts, *, min_views, since):
    return posts.annotate(
        recent_views=Count("views", filter=Q(views__created_at__gte=since), distinct=True),
        comment_count=Count("comments", distinct=True),
    ).filter(recent_views__gt=min_views).order_by("-comment_count", "pk")
```

## Using Arel

For reusable, composable query fragments:

```python
def search_posts(posts, *, query):
    return posts.filter(Q(title__icontains=query) | Q(body__icontains=query))
```

## Attaching Query Objects as Scopes

```python
# Pass a scope explicitly; do not patch the base model or infer query classes.
posts = trending_posts(authorized_posts(actor), min_views=50, since=yesterday)
```

## Anti-Patterns

### Over-Scoping

Scopes that include other scopes, causing conflicts:

```python
# Bad: each method silently resets ordering; the last order_by wins in Django.
posts = Post.objects.order_by("-created_at").order_by("-views_count")
```

### Context-Free Queries in Models

General queries that are actually context-specific:

```python
def search_admin_users(users, *, query):
    return users.filter(Q(username__icontains=query) | Q(posts__title__icontains=query)).distinct()
```

## Related Mechanisms

| Mechanism | Purpose |
|-----|---------|
| arel-helpers | Reduce Arel boilerplate for complex JOINs |
