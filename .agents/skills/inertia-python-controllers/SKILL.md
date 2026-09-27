---
name: inertia-python-controllers
description: Django views for Inertia and React with explicit rendering, safe props, shared data, deferred/partial loading, session errors, Django messages, 303 redirects, CSRF and authorization. Use for changing page responses or mutation contracts.
---

## Project Contract

- Read config/settings.py, config/middleware.py, config/http.py and the caller first.
  This repository uses inertia-django 2 and @inertiajs/react 3, with explicit page names.
- Server examples below illustrate feature contracts, not preinstalled routes or models.
  Django views return render(request, component, props=...). Never serialize a model
  or QuerySet implicitly; build a bounded allowlist first.
- Use trailing-slash Django routes. The starter mutations are POST endpoints; Django
  does not automatically parse multipart PATCH/PUT bodies or Rails _method overrides.
- Supply the shared csrfToken as X-CSRFToken for mutations; config/http.py validates
  supported JSON or form bodies. A Form component alone does not configure Django CSRF.
  Do not also configure automatic XSRF injection for the same header: the client
  can append both values, producing a token Django rejects.
- Validation uses redirect-after-POST and one-use errors in shared props.
  Messages use page.flash.messages, an array of {level, message}; there are no
  notice/alert keys. See the actual web/src/types.ts contract.
- Frontend-only Vue/Svelte references preserve upstream alternatives; this starter
  installs React. Rails-only generators and implicit resource lookup do not apply.


# Inertia Django Controllers

Server-side patterns for Django views serving Inertia responses.

**Before adding a prop, ask:**
- **Needed on every page?** → `share(request, ...)` in a base controller (`InertiaController`), not a per-action prop
- **Expensive to compute?** → `defer` — page loads fast, data streams in after
- **Only needed on partial reload?** → `optional` — skipped on initial load
- **Reference data that rarely changes?** → `once` — cached across navigations

**NEVER:**
- Redirect an Inertia request to an external provider with an ordinary 302; use location.
- Flatten form errors into an unkeyed list; preserve field names.
- Serialize arbitrary model attributes or infer a page from a view name.
- Assume React Form configures Django CSRF or body parsing automatically.

## Render Syntax

Django views always return an explicit response. Use
`render(request, "Users/Index", props={"users": safe_users})` for a data page
and `render(request, "About", props={})` for a static page.
There is no default_render option or automatic instance-variable serialization.

```python
from inertia import render, defer

def index(request):
    return render(request, "Users/Index", props={
        "users": users_data(request.user),
        "stats": defer(lambda: expensive_stats(request.user)),
    })

# Even static pages require an explicit HttpResponse.
def about(request):
    return render(request, "About", props={})
```

## Prop Types

Import helpers from inertia. Call them with values or zero-argument callables.

| Type | Syntax | Behavior |
|---|---|---|
| Regular | `{"key": value}` | Evaluated before render; selected props included |
| Lazy | `lambda: expensive_value()` | Evaluated only when selected |
| Optional | `optional(lambda: value())` | Requested partial reloads only |
| Deferred | `defer(lambda: value(), group="analytics")` | Loaded in a later request |
| Once | `once(lambda: value(), expires_at=60)` | Client reuse with explicit expiry |
| Merge | `merge(lambda: values(), match_on="id")` | Partial response accumulation |
| Deep merge | `deep_merge(lambda: value())` | Partial nested merge |
| Always | `always(lambda: value())` | Included even on partial reloads |
| Scroll | `scroll(lambda: rows(), metadata)` | Pagination metadata for InfiniteScroll |

```python
return render(request, "Messages/Index", props={
    "filters": validated_filters,
    "messages": lambda: message_summaries(messages_scope),
    "stats": defer(lambda: dashboard_stats(actor=request.user)),
    "chart": defer(lambda: dashboard_chart(actor=request.user), group="analytics"),
    "countries": once(lambda: list(Country.objects.values("name", "code"))),
    "posts": merge(lambda: post_summaries(posts_scope), match_on="id"),
    "csrfToken": always(lambda: get_token(request)),
})
```

### Deferred Props — Full Stack Example

Server defers slow data, client shows fallback then swaps in content:

```python
def show(request):
    return render(request, "Dashboard", props={
        "basic_stats": quick_summary(request.user),
        "analytics": defer(lambda: compute_analytics(request.user)),
    })
```

```tsx
// Page component — child reads deferred prop from page props
import { Deferred, usePage } from '@inertiajs/react'

export default function Dashboard({ basic_stats }: Props) {
  return (
    <>
      <QuickStats data={basic_stats} />
      <Deferred data="analytics" fallback={<div>Loading analytics...</div>}>
        <AnalyticsPanel />
      </Deferred>
    </>
  )
}

function AnalyticsPanel() {
  const { analytics } = usePage<{ analytics: Analytics }>().props
  return <div>{analytics.revenue}</div>
}
```

## Shared Data

Use `share(request, ...)` in controllers — it needs controller context (`current_user`,
request). The initializer only handles `config.*` settings (version, Django messages).

```python
def shared_props(get_response):
    def middleware(request):
        user = user_summary(request.user) if request.user.is_authenticated else None
        share(request, app_name="MyApp", auth={"user": user})
        if request.user.is_authenticated:
            share(request, notifications=lambda: unread_count(request.user))
        return get_response(request)
    return middleware
```

Lambda and action-scoped variants are in [`references/configuration.md`](references/configuration.md).

**Evaluation order:** Multiple `share(request, ...)` calls merge top-down. If a child
controller shares the same key as a parent, the child's value wins. Block and lambda
shares are lazily evaluated per-request — they don't run for non-Inertia requests.

## Flash Messages

Flash is automatic. Configure exposed keys if needed:

```python
# Django SessionMiddleware and MessageMiddleware precede InertiaMiddleware.
# Public messages become {"messages": [{"level": "success", "message": "Created"}]}.
# There is no Django messages_keys setting.
```

Use standard Django messages in controllers:
```python
messages.success(request, "User created")
return redirect_303("users")
# For a public error message: messages.error(request, "Could not complete this action").
```

## Redirects & Validation Errors

After create/update/delete, return 303 through redirect_303. Validation errors
are stored for the redirected GET; malformed body structure returns 400:

```python
@require_POST
@login_required
def create(request):
    form = UserForm(form_input(request, fields={"name", "email"}))
    if not form.is_valid():
        return invalid_form(request, form, destination="user-new")
    create_user(actor=request.user, **form.cleaned_data)
    messages.success(request, "Created")
    return redirect_303("users")
```

The starter maps each form field to its first error string, including `__all__`
for non-field errors. Keys must match input names and the TypeScript errorValueType.
Render non-field errors in a visible form-level region.

## Authorization as Props

Pass permissions as per-resource `can` hash — frontend controls visibility,
server enforces access. See `inertia-python-controllers` + `inertia-python-pages` skills.

**MANDATORY — READ ENTIRE FILE** when implementing authorization props:
[`references/authorization.md`](references/authorization.md) (~40 lines) — full-stack
`can` pattern with explicit Django policies.

**Do NOT load** if not passing permission data to the frontend.

## External Redirects (`location`)

**CRITICAL:** `redirect` for external URLs breaks Inertia — the client
receives a 302 but tries to handle it as an Inertia response (JSON), not a
full page redirect. `location` returns 409 with `X-Inertia-Location`
header, which tells the client to do `window.location = url`.

```python
from inertia import location

@require_POST
@login_required
def checkout(request):
    session = payment_provider.create_checkout(actor=request.user)
    # Validate an external destination against the provider contract, never raw input.
    return location(session.url)
```

Use `location` for any URL outside the Inertia app: payment
providers, OAuth, external services.

## History Encryption

Encrypts page data in browser history state — `INERTIA_ENCRYPT_HISTORY = not DEBUG`.
Call `inertia.http.clear_history(request)` on logout/role change.
Full setup with server-side and client-side examples is in
[`references/configuration.md`](references/configuration.md).

## Configuration

See [`references/configuration.md`](references/configuration.md) for all
Django INERTIA_* settings options (version, encrypt_history, Django messages, etc.).

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 302 loop on Stripe/OAuth redirect | `redirect` for external URL | Use `location` — it returns 409 + `X-Inertia-Location` header |
| Errors don't display next to fields | Error keys don't match input `name` | Form error keys must match input `name` attributes exactly |
| Frontend route mismatch | URL differs from urls.py | Update callers and route smoke tests together; no route generator is installed |

## Related Skills
- **Form error display** → `inertia-python-forms`
- **Flash toast UI** → `inertia-python-pages` (access) + `shadcn-inertia` (Sonner)
- **Deferred on client** → `inertia-python-pages` (`<Deferred>` component)
- **Type-safe props** → `inertia-python-typescript` or `python-serialization` (serializers)
- **Testing** → `inertia-python-testing`

## References

**MANDATORY — READ ENTIRE FILE** when using advanced prop types (`merge`,
`scroll`, `deep_merge`) or combining multiple prop options:
[`references/prop-types.md`](references/prop-types.md) (~180 lines) — detailed behavior,
edge cases, and combination rules for all prop types.

**Do NOT load** `prop-types.md` for basic `defer`, `optional`, `once`, or `always`
usage — the table above is sufficient.

Load [`references/configuration.md`](references/configuration.md) (~180 lines) only when
setting up Django INERTIA_* settings for the first time or debugging configuration
issues. **Do NOT load** for routine controller work.
