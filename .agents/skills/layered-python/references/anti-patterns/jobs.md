# Job Anti-Patterns

Background-job classes that add boilerplate without value.

## Anemic Jobs

**Problem:** Job classes that just delegate to a single model method.

```python
# Bad: an extra model wrapper hides enqueueing and fixes a transport in the model.
class Post(models.Model):
    def notify_recipients_later(self):
        notify_recipients_task.enqueue(self.pk)
```

**Issues:**
- Boilerplate job files cluttering `app/jobs`
- Two places to maintain (job + model method)
- Job class adds no value beyond async execution
- Makes the jobs folder noisy, hiding complex jobs that need attention

**Signal:** Job's `perform` method is a single line calling a method on the argument.

**Fix:** Keep a thin, explicit worker entry point. A few lines are justified when
they establish deserialization, access, idempotency, retries and observability.
Do not install runtime method-generation merely to remove a wrapper.

```python
def notify_recipients_job(*, post_id):
    post = Post.objects.get(pk=post_id)
    notify_recipients(post=post)
```

Queue and retry configuration belongs to the selected backend; the starter does
not install a worker. Missing-record behavior must be deliberate and observable.

**With options:**
```python
def notify_recipients_job(*, post_id, delivery_id):
    post = Post.objects.get(pk=post_id)
    delivery = DeliveryIntent.objects.get(pk=delivery_id, post_id=post_id)
    deliver_once(post=post, delivery=delivery)
```

**When to keep separate job class:**
- Job has complex logic beyond single method call
- Job processes multiple records with custom batching
- Job needs extensive retry/error handling configuration
- Job is triggered from multiple unrelated models
