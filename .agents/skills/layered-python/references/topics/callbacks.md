# Callbacks

## Contents

- Summary
- Callback Scoring System
- Good Callbacks (4-5/5)
- Problematic Callbacks (1-2/5)
- Callback Anti-Patterns
- When Callbacks ARE Appropriate
- Callback to Service Extraction
- Testing Callback-Light Models

## Summary

Callbacks are hooks into object lifecycle events. Django exposes signals and overridable model methods; overuse leads to tangled dependencies and hidden behavior. Signals are not a reliable invariant boundary: bulk operations bypass save signals, and save does not run full_clean(). Use callbacks judiciously, preferring explicit operations.

## Callback Scoring System

Rate callbacks on a 5-point scale:

| Score | Type | Description | Example |
|-------|------|-------------|---------|
| 5/5 | Transformer | Pure data transformation | `Form.clean() :normalize_email` |
| 4/5 | Maintainer | Internal consistency | `pre_save receiver :update_cached_count` |
| 3/5 | Timestamp | Set time-based attributes | `pre_save receiver :set_published_at` |
| 2/5 | Background trigger | Enqueue async work | `transaction.on_commit :enqueue_indexing` |
| 1/5 | Operation | Synchronous side effects | `post_save receiver :send_welcome_email` |

**Rule**: Avoid callbacks scoring below 3/5. Extract to explicit service objects.

## Good Callbacks (4-5/5)

### Transformers

```python
class RegistrationForm(forms.Form):
    email = forms.EmailField()
    name = forms.CharField(max_length=100)

    def clean_email(self):
        email = self.cleaned_data["email"]
        local, domain = email.rsplit("@", 1)
        return f"{local}@{domain.lower()}"
```

### Maintainers

```python
# Read-time aggregation cannot drift from bulk writes or skipped signals.
posts = Post.objects.annotate(comment_count=Count("comments"))
```

### Safe Timestamps

```python
def publish_article(article, *, at):
    article.published_at = at
    article.full_clean()
    article.save(update_fields=["published_at"])
```

## Problematic Callbacks (1-2/5)

### Background Triggers (2/5)

```python
@transaction.atomic
def update_post(*, post, title):
    post.title = title
    post.save(update_fields=["title"])
    transaction.on_commit(partial(enqueue_indexing, post.pk))
# Use durable intent instead if losing enqueue on a crash is unacceptable.
```

### Operations (1/5) — Extract These

```python
@transaction.atomic
def register_user(*, username, password):
    user = User.objects.create_user(username=username, password=password)
    Workspace.objects.create(owner=user, name="My Workspace")
    DeliveryIntent.objects.create(user=user, event="registered")
    return user
```

## Callback Anti-Patterns

### Conditional Complexity

```python
@transaction.atomic
def request_order_completion(*, order_id):
    order = Order.objects.select_for_update().get(pk=order_id)
    order.request_completion()
    order.save(update_fields=["status"])
    PaymentIntent.objects.create(order=order, idempotency_key=str(order.pk))
# Charge outside SQL in a worker, reconcile the provider result, then complete.
# Database rollback cannot undo an external payment.
```

### Callback Chains

```python
# Hidden save-signal chains are avoided with an explicit operation or aggregate.
authors = Author.objects.annotate(post_count=Count("posts"))
```

### Testing Difficulties

```python
user = User.objects.create_user(username="test")  # No implicit email.
# The registration operation is tested separately for committed delivery intent.
```

### Skip Callback Temptation

```python
# Do not disconnect/reconnect global signal receivers to create test data.
user = User.objects.create_user(username="fixture")
```

## When Callbacks ARE Appropriate

1. **Data normalization** — cleaning input before save
2. **Derived attributes** — calculating values from other attributes
3. **Internal state consistency** — keeping model internally valid
4. **Soft deletes** — setting timestamps on destroy

```python
class Document(models.Model):
    def prepare(self):
        self.filename = slugify(self.filename)
        self.word_count = len(self.content.split())

    def soft_delete(self, *, at):
        self.deleted_at = at
        self.save(update_fields=["deleted_at"])
```

## Callback to Service Extraction

Before (callbacks):

```python
# Bad: these receivers turn a database save into unrelated external work.
post_save.connect(notify_subscribers, sender=Article)
post_save.connect(sync_to_search, sender=Article)
post_delete.connect(cleanup_attachments, sender=Article)
```

After (services):

```python
def create(request):
    form = ArticleForm(request.POST)
    if not form.is_valid():
        return invalid_form(request, form, destination="article-new")
    article = create_article(actor=request.user, **form.cleaned_data)
    return redirect_303("article-detail", article_id=article.pk)
```

## Testing Callback-Light Models

```python
def test_email_domain_normalization():
    form = RegistrationForm({"email": "Person@EXAMPLE.COM", "name": "Person"})
    assert form.is_valid()
    assert form.cleaned_data["email"] == "Person@example.com"

@pytest.mark.django_db
def test_registration_records_delivery():
    user = register_user(username="alice", password="test-password")
    assert DeliveryIntent.objects.filter(user=user, event="registered").exists()
```
