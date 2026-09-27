# Flash Toast with Sonner

Full-stack flash toast: Django messages + useFlash hook + Sonner.

Use messages.success or messages.error on the server. Each public message is a
{level, message} entry in page.flash.messages. Keep FlashData aligned.

## Django Setup

The adapter reads Django message storage:

```python
# SessionMiddleware and MessageMiddleware precede InertiaMiddleware.
# No flash_keys configuration: page.flash.messages contains level/message records.
```

Use the Django messages API; do not duplicate messages in props:

```python
def create(request):
    form = UserForm(form_input(request, fields={"name", "email"}))
    if not form.is_valid():
        return invalid_form(request, form, destination="user-new")
    create_user(actor=request.user, **form.cleaned_data)
    messages.success(request, "User created")
    return redirect_303("users")
```

## useFlash Hook

**Important:** `toast` is imported from `'sonner'` (the package), NOT from `@/components/ui/sonner` (that only exports `Toaster`).

```tsx
// web/hooks/use-flash.ts
import { router, usePage } from '@inertiajs/react'
import { useEffect, useRef } from 'react'
import { toast } from 'sonner' // NOT from '@/components/ui/sonner'

function showFlash(flash: FlashData) {
  for (const item of flash.messages ?? []) {
    if (item.level === "error") toast.error(item.message)
    else toast(item.message)
  }
}

export function useFlash() {
  const { flash } = usePage()
  const toastShowed = useRef(false)

  // Show flash from initial page load
  useEffect(() => {
    if (!toastShowed.current) {
      toastShowed.current = true
      showFlash(flash)
    }
  }, [flash])

  // Listen for flash events (client-side flash, redirects)
  useEffect(() => {
    return router.on('flash', (event) => {
      showFlash(event.detail.flash)
    })
  }, [])
}
```

## Layout Integration

Use in persistent layout (runs once, covers all pages):

```tsx
// web/layouts/persistent-layout.tsx
import { Toaster } from 'sonner'
import { useFlash } from '@/hooks/use-flash'

export function PersistentLayout({ children }) {
  useFlash()
  return <>{children}<Toaster /></>
}
```
