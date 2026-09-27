# Inertia Django Configuration

## Table of Contents

- [Initializer](#initializer)
- [Version Tracking](#version-tracking)
- [Flash Keys](#flash-keys)
- [History Encryption](#history-encryption)
- [Error Handling](#error-handling)
- [SSR Configuration](#ssr-configuration)
- [Middleware](#middleware)

---

## Initializer

```python
# config/settings.py
from django.core.serializers.json import DjangoJSONEncoder
INERTIA_LAYOUT = "base.html"
INERTIA_VERSION = os.environ["ASSET_VERSION"]
INERTIA_ENCRYPT_HISTORY = not DEBUG
INERTIA_JSON_ENCODER = DjangoJSONEncoder
# All page names and safe props are passed explicitly to render().
```

## Version Tracking

Inertia uses version tracking to detect asset changes and trigger
full page reloads when the frontend bundle changes.

```python
# Production release identifier, changed with frontend assets.
INERTIA_VERSION = os.environ["ASSET_VERSION"]
```

## Flash Keys

Django messages are emitted as page.flash.messages; only put public text into messages.

```python
# Django messages are exposed automatically. Message bodies must be public.
messages.success(request, "Saved")
messages.error(request, "Could not save")
```

Access on client: `usePage().flash.messages`, an optional array of {level, message}.

## History Encryption

Encrypts page data in browser history state. Without it, sensitive props are
stored in plaintext and visible via back/forward navigation or devtools.

**Enable in production only** — encryption can cause issues with HMR and
hot-reloading in development:

```python
INERTIA_ENCRYPT_HISTORY = not DEBUG
```

**Clear history** on logout to prevent back-button access to authenticated pages:

```python
from django.contrib.auth import logout
from inertia.http import clear_history

def sign_out(request):
    logout(request)
    clear_history(request)
    return redirect_303("login")
```

```tsx
// Client-side — clear history programmatically (rotates encryption key)
import { router } from '@inertiajs/react'
router.clearHistory()
```

**When to use `clear_history`:** logout, role change, account switching — any
moment when the previous session's data should not be accessible via back button.

## Error Handling

```python
# Shared middleware owns the one-request validation error lifecycle.
share(request, errors=always(lambda: request.session.pop("form_errors", {})))
# The starter preserves errors if an asset-version mismatch requires a fresh visit.
```

Custom error page for non-Inertia requests:
```python
def not_found(request, exception):
    # Use a generic public message; do not expose database identifiers or exceptions.
    return render(request, "Errors/NotFound", props={"message": "Not found"}, status=404)
# Register handler404 in urls.py only after implementing the React page.
```

## SSR Configuration

```python
# Only enable after deploying and testing an actual SSR entrypoint/service.
INERTIA_SSR_ENABLED = True
INERTIA_SSR_URL = "http://localhost:13714"
```

Vite SSR setup:
```ts
// vite.config.ts
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  ssr: {
    noExternal: ['@inertiajs/react'],
  },
})
```
