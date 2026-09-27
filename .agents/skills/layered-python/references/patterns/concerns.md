# Concerns

## Contents

- Summary
- When to Use
- When NOT to Use
- Key Principles
- Concern Health Check
- Implementation
- Concern vs Other Patterns
- Testing Concerns
- Anti-Patterns
- File Organization
- Concern Checklist

## Summary

A cohesive module or collaborator is the Python equivalent of a concern. Use a small cooperative mixin only when its required fields and super() contract are explicit. Do not register signals as a hidden import side effect.

## When to Use

- Shared behavior across multiple models
- Cohesive feature sets (soft delete, auditing, slugging)
- Interface extraction (common protocol for different models)
- Reducing model file size while maintaining cohesion

## When NOT to Use

- Single-model "organization" (hiding complexity)
- Unrelated methods grouped together
- Callbacks that should be explicit operations
- As a substitute for proper abstractions

## Key Principles

- **Cohesion over organization** — concerns group related behavior, not random methods
- **Explicit dependencies** — document what the including class must provide
- **Test concerns independently** — don't rely on specific model setup
- **Prefer composition** — consider service objects before concerns

## Concern Health Check

Signs of healthy concerns:

```python
class Sluggable(models.Model):
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True

    def assign_slug(self, *, title):
        self.slug = slugify(title)
# Call explicitly before full_clean/save; the database enforces uniqueness.
```

Signs of unhealthy concerns:

```python
# Bad: a mixin combines unrelated responsibilities and triggers external effects.
class PostExtensions:
    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        notify_followers(self.pk)
        sync_to_search(self.pk)
        return result
```

## Implementation

### Basic Concern

```python
class SoftDeleteQuerySet(models.QuerySet):
    def kept(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

class SoftDeletable(models.Model):
    deleted_at = models.DateTimeField(null=True)
    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def soft_delete(self, *, at):
        self.deleted_at = at
        self.save(update_fields=["deleted_at"])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
```

### Concern with Configuration

```python
@transaction.atomic
def update_post(*, actor, post_id, title):
    post = Post.objects.select_for_update().get(pk=post_id)
    previous_title = post.title
    post.title = title
    post.full_clean()
    post.save(update_fields=["title"])
    AuditLog.objects.create(post=post, actor=actor, changes={"title": [previous_title, title]})
    return post
```

### Concern with Required Interface

```python
class Publishable(models.Model):
    published_at = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def publish(self, *, at):
        self.published_at = at

# Notification orchestration stays outside the shared domain behavior.
```

### Interface Extraction

```python
class PostQuerySet(models.QuerySet):
    def search(self, query):
        return self.filter(Q(title__icontains=query) | Q(body__icontains=query))

class UserQuerySet(models.QuerySet):
    def search(self, query):
        return self.filter(Q(username__icontains=query) | Q(email__icontains=query))
# Small duplication is clearer than a mutable generic field-registration DSL.
```

## Concern vs Other Patterns

| Need | Pattern |
|------|---------|
| Shared query logic | Query object |
| Cross-cutting callbacks | Service object |
| State-dependent behavior | State machine |
| External API integration | Service object |
| Shared validations | Concern (carefully) |
| Shared associations | Concern |

## Testing Concerns

```python
@pytest.mark.django_db
def test_soft_delete_changes_explicit_scope(post):
    post.soft_delete(at=timezone.now())
    assert post.deleted_at is not None
    assert not Post.objects.kept().filter(pk=post.pk).exists()
    assert Post.objects.deleted().filter(pk=post.pk).exists()
```

## Anti-Patterns

### Single-Model Concerns

```python
# A single model's cohesive behavior usually stays on that model.
post.publish(at=timezone.now())
post.save(update_fields=["published_at"])
```

### Dependency Hiding

```python
@transaction.atomic
def publish_post(*, post):
    post.publish(at=timezone.now())
    post.save(update_fields=["published_at"])
    transaction.on_commit(partial(notify_followers, post.pk))
```

### Concern Chains

```python
# Name composed dependencies explicitly; do not mutate bases or register hooks.
contact = ContactInformation(user=user)
publication = PublicationWorkflow(post=post)
```

## File Organization

```
<feature>/models/
├── concerns/
│   ├── auditable.py
│   ├── publishable.py
│   ├── searchable.py
│   └── soft_deletable.py
├── post.py
└── user.py
```

## Concern Checklist

Before creating a concern, verify:

- [ ] Will multiple models use this?
- [ ] Are all methods cohesively related?
- [ ] Is the interface documented?
- [ ] Could this be a service object instead?
- [ ] Are callbacks necessary or hiding complexity?
