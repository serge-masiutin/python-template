# Concern Anti-Patterns

Misuses of `cooperative Python mixins` that hide structural problems.

## Code-Slicing Concerns

**Problem:** Splitting model by framework artifact type, not behavior.

```python
class ContactMixin:
    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        validate_email(self.email)
        return super().save(*args, **kwargs)

    def full_contact_info(self):
        return f"{self.email} / {self.phone}"
```

**Test:** If removing this concern breaks unrelated tests, it's code-slicing.

**Fix:** Keep in model or extract to value object.

```python
class Publishable(models.Model):
    published_at = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def publish(self, *, at):
        self.published_at = at

    @property
    def is_published(self):
        return self.published_at is not None
```

## Overgrown Concerns

**Problem:** Concern has too many responsibilities.

```python
class WithMedia:
    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        process_images(self.pk)
        generate_thumbnail(self.pk)
        transcode_videos(self.pk)
        return result
```

**Fix:** Extract to delegate object or separate concerns.

```python
def process_media(*, post_id, images, thumbnails, videos):
    images.process(post_id)
    thumbnails.generate(post_id)
    videos.transcode(post_id)
```
