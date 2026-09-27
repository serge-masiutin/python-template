# Callback Analysis Workflow

Deep analysis of Django ORM callbacks. Audits callbacks using a 5-tier scoring system, identifies extraction candidates, and recommends moving operation callbacks to explicit service objects.

## Contents

- [Callback Scoring System](#callback-scoring-system)
- [Analysis Process](#analysis-process)
- [Output Format](#output-format)
- [Extraction Patterns](#extraction-patterns)
- [Related](#related)

## Callback Scoring System

### 5/5 - Transformer (Keep)
Pure data transformation on the same object.

```python
def clean_email(self):
    return User.objects.normalize_email(self.cleaned_data["email"])
```

### 4/5 - Maintainer (Keep)
Maintains internal object consistency.

```python
posts = Post.objects.annotate(comment_count=Count("comments"))
```

### 3/5 - Timestamp (Acceptable)
Sets time-based attributes.

```python
def publish(self, *, at):
    self.published_at = at
```

### 2/5 - Background Trigger (Consider Extracting)
Enqueues background work.

```python
transaction.on_commit(partial(enqueue_indexing, record.pk))
# Assess loss between commit and enqueue; use durable intent if needed.
```

### 1/5 - Operation (Extract)
Synchronous side effects, external communication.

```python
post_save.connect(send_welcome_email, sender=User)
post_save.connect(create_default_records, sender=User)
post_save.connect(sync_to_external_api, sender=User)
```

## Analysis Process

### 1. Find All Callbacks

```python
CALLBACK_PATTERNS = ("pre_save", "post_save", "pre_delete", "post_delete", "m2m_changed",
                     "post_init", "receiver", "on_commit", "def save(", "def delete(", "def ready(")
```

### 2. Score Each Callback

For each callback found:
1. Read the callback method body
2. Classify by what it does
3. Assign score
4. Note extraction recommendation

### 3. Identify Callback Chains

Look for models with multiple related callbacks:

```python
post_save.connect(create_profile, sender=User)
post_save.connect(send_welcome_email, sender=User)
post_save.connect(notify_admin, sender=User)
post_save.connect(track_signup, sender=User)
```

### 4. Check for Skip Patterns

Search for callback skipping (indicates design smell):

```python
# Red flag: changing process-global receiver registration to bypass effects.
post_save.disconnect(send_email, sender=User)
user.save()
post_save.connect(send_email, sender=User)
```

## Output Format

```markdown
# Callback Analysis Report

## Summary
- Total callbacks: 47
- Score 5/5 (keep): 12
- Score 4/5 (keep): 8
- Score 3/5 (acceptable): 5
- Score 2/5 (consider): 7
- Score 1/5 (extract): 15

## By Model

### User (<feature>/models/user.py)
| Line | Callback | Method | Score | Action |
|------|----------|--------|-------|--------|
| 15 | Form.clean() | normalize_email | 5/5 | Keep |
| 16 | Form.clean() | strip_whitespace | 5/5 | Keep |
| 18 | post_save receiver | send_welcome_email | 1/5 | Extract |
| 19 | post_save receiver | create_profile | 1/5 | Extract |
| 20 | post_save receiver | notify_admin | 1/5 | Extract |

**Recommendation**: Create `CreateUser` service to handle registration flow.

### Order (<feature>/models/order.py)
| Line | Callback | Method | Score | Action |
|------|----------|--------|-------|--------|
| 22 | pre_save receiver | calculate_totals | 4/5 | Keep |
| 25 | post_save receiver | update_inventory | 1/5 | Extract |
| 26 | post_save receiver | charge_payment | 1/5 | Extract |
| 27 | transaction.on_commit | send_confirmation | 2/5 | Consider |

**Recommendation**: Create `CompleteOrder` service for post-save operations.

## Callback Chains

### User Registration Chain
```
post_save receiver :send_welcome_email
post_save receiver :create_profile
post_save receiver :create_default_workspace
post_save receiver :notify_admin
post_save receiver :track_signup_analytics
```

**Recommendation**: Extract to `create_user` service:
```python
@transaction.atomic
def register_user(*, username, password):
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.create(user=user)
    Workspace.objects.create(owner=user, name="Default")
    DeliveryIntent.objects.create(user=user, event="registered")
    return user
```

## Skip Callback Usage

Found 3 instances of callback skipping:

1. `tests/user_test.py:45` - Test setup
2. `<feature>/operations/bulk_import.py:78` - Bulk operation
3. `lib/tasks/migrate.rake:23` - Data migration

**Assessment**: Skip usage in tests is acceptable. Production code skipping suggests callback design issues.

## Extraction Priority

### High Priority (Extract Now)
1. **User** - 5 operation callbacks, clear service extraction
2. **Order** - Payment and inventory callbacks

### Medium Priority (Plan Extraction)
1. **Post** - Publication and notification callbacks
2. **Comment** - Notification callbacks

### Low Priority (Monitor)
1. **Profile** - Single background job callback
```

## Extraction Patterns

### Before: Callback Chain
```python
@receiver(post_save, sender=User)
def hidden_registration(sender, instance, created, **kwargs):
    if created:
        send_welcome_email(instance.pk)
        Profile.objects.create(user=instance)
        notify_admin(instance.pk)
```

### After: Service Object
```python
@transaction.atomic
def register_user(*, username, password):
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.create(user=user)
    transaction.on_commit(partial(send_welcome_email, user.pk))
    transaction.on_commit(partial(notify_admin, user.pk))
    return user
```

## Related

- [Callbacks topic](../references/topics/callbacks.md)
- [Service Objects pattern](../references/patterns/service-objects.md)
- [Extraction signals](../references/core/extraction-signals.md)
- [Callbacks-to-service example](../examples/callbacks-to-service.md)
