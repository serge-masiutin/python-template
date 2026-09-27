# Repositories

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Repository vs Query Object
- Testing
- Anti-Patterns
- File Organization

## Summary

Repositories are a **last-resort** data-access pattern in Django. Prefer simpler tools first:

1. **Django ORM class methods / scopes** — for single-model queries and simple filters.
2. **Query objects** — for composable, parameterized query building across one or more models.
3. **Repositories** — only when you need to return **custom domain objects** mapped from Django ORM data, decoupled from the AR schema.

The repository's value is the *mapping boundary*: callers receive plain Python objects (`Data`, `Struct`, Python objects) with stable shapes, not Django model instances. If you're returning Django model instances as-is, you don't need a repository — a scope or query object will do.

## When to Use

- Returning **custom domain objects** mapped from ORM data (the primary case)
- Complex multi-model reads where the result shape differs from any Django model
- Aggregation from multiple sources (DB + cache + external API) into a unified domain object
- Read-model optimization (CQRS-lite) where the read shape diverges from the write model

## When NOT to Use

- Simple single-model queries → use scopes / class methods
- Composable, parameterized queries → use query objects
- CRUD operations → use Django ORM directly
- Returning Django model instances as-is → just expose them via scopes (no mapping = no repository)
- Before mapping needs justify the abstraction

## Key Principles

- **Mapping is the point** — every method returns a domain object, not an Django model instance
- **Complement Django ORM** — don't fight Django conventions; build on top
- **Encapsulate complexity** — hide multi-model joins, aggregations, external lookups
- **Single responsibility** — one repository per aggregate or read concern

## Implementation

### Basic Repository

```python
def featured_posts(posts):
    return posts.filter(published_at__isnull=False).annotate(
        comments_count=Count("comments", distinct=True), likes_count=Count("likes", distinct=True)
    ).order_by("-likes_count", "pk")[:10]
# This still returns a QuerySet; call it a query, not a repository abstraction.
```

### Repository with Caching

```python
def dashboard_stats(*, user):
    posts = Post.objects.filter(author=user)
    counts = posts.aggregate(total=Count("pk"), published=Count("pk", filter=Q(published_at__isnull=False)),
                             views=Sum("views_count", default=0))
    comments = Comment.objects.filter(post__in=posts).count()
    return {**counts, "engagement": comments / counts["views"] if counts["views"] else 0}
# Add caching only after measurement and an explicit invalidation/freshness contract.
```

### Multi-Source Repository

```python
@dataclass(frozen=True)
class Activity:
    kind: str
    record_id: int
    created_at: datetime
    description: str


def recent_activity(*, user):
    posts = [Activity("post", p.pk, p.created_at, f"Published {p.title}") for p in user.posts.order_by("-created_at")[:20]]
    comments = [Activity("comment", c.pk, c.created_at, f"Commented on {c.post.title}")
                for c in user.comments.select_related("post").order_by("-created_at")[:20]]
    likes = [Activity("like", like.pk, like.created_at, f"Liked {like.post.title}")
             for like in user.likes.select_related("post").order_by("-created_at")[:20]]
    return sorted(posts + comments + likes, key=lambda item: item.created_at, reverse=True)[:20]
```

### Read Model Repository

For complex reporting or dashboards:

```python
@dataclass(frozen=True)
class Performance:
    day: date
    posts_count: int
    comments_count: int
    likes_count: int
    total_views: int

    def engagement_rate(self):
        return 100 * (self.comments_count + self.likes_count) / self.total_views if self.total_views else 0
# Aggregate each relation independently before combining; joining both comments
# and likes before SUM(views_count) multiplies rows and inflates totals.
```

### External Data Integration

```python
@dataclass(frozen=True)
class BookWithMetadata:
    book: Book
    cover_url: str
    description: str
    rating: Decimal


def find_book_with_metadata(*, isbn, client):
    book = Book.objects.get(isbn=isbn)
    metadata = client.fetch_book(isbn=isbn)  # Adapter validates response schema.
    return BookWithMetadata(book, metadata.cover_url, metadata.description, metadata.rating)
# Cross-source composition returns an explicit value, not fake unsaved ORM rows.
```

## Repository vs Query Object

| Repository | Query Object |
|------------|--------------|
| Multiple related queries | Single query concern |
| Cross-model aggregation | Single-model filtering |
| External data integration | Database queries only |
| Caching strategies | Composable query logic |
| Read model concerns | Reusable query fragments |

```python
published = Post.objects.filter(author=actor, published_at__isnull=False).order_by("-published_at")
book = find_book_with_metadata(isbn=isbn, client=books_client)
```

## Testing

```python
@pytest.mark.django_db
def test_dashboard_counts(user, published_posts, draft_posts):
    counts = dashboard_stats(user=user)
    assert counts["total"] == 5
    assert counts["published"] == 3
```

## Anti-Patterns

### Thin Repository Wrapper

```python
# No repository is needed to wrap a direct ORM query.
post = Post.objects.get(pk=post_id)
```

### Repository with Business Logic

```python
@transaction.atomic
def publish_post(*, post_id):
    post = Post.objects.select_for_update().get(pk=post_id)
    post.publish(at=timezone.now())
    post.save(update_fields=["published_at"])
    transaction.on_commit(partial(notify_subscribers, post.pk))
    return post
```

## File Organization

```
app/
├── models/
│   └── post.py
├── queries/
│   └── published_posts_query.py
└── repositories/
    ├── dashboard_repository.py
    ├── analytics_repository.py
    └── post_repository.py
```
