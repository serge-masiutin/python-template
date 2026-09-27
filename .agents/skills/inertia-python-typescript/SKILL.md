---
name: inertia-python-typescript
description: >-
  TypeScript type safety for Inertia Django (React, Vue, Svelte): shared props, flash, and errors via InertiaConfig
  module augmentation in globals.d.ts. Use when setting up TypeScript types, configuring shared props typing, fixing
  TS2344 or TS2339 errors in Inertia components, or adding new shared data.
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


# Inertia Django TypeScript Setup

Type-safe shared props, flash, and errors using InertiaConfig module augmentation.
Works identically across React, Vue, and Svelte — the `globals.d.ts` and `InertiaConfig` setup is the same for all frameworks.

**Before adding TypeScript types, ask:**
- **Shared props (auth, flash)?** → Update `SharedProps`/`FlashData` in `index.ts` — InertiaConfig in `globals.d.ts` propagates them globally via `usePage()`
- **Page-specific props?** → `type Props = { ... }` in the page file only — never include shared props here

## InertiaConfig Module Augmentation

Define shared props type ONCE globally — never in individual page components.

InertiaConfig property names are EXACT — do not rename them:
- `sharedPageProps` (NOT sharedProps)
- `flashDataType` (NOT flashProps, NOT flashData)
- `errorValueType` (NOT errorBag, NOT errorType)

```typescript
// web/src/types/globals.d.ts
import type { FlashData, SharedProps } from '@/types'

declare module '@inertiajs/core' {
  export interface InertiaConfig {
    sharedPageProps: SharedProps   // EXACT name — auto-typed for usePage().props
    flashDataType: FlashData      // EXACT name — auto-typed for usePage().flash
    errorValueType: string      // EXACT name — errors are first-message strings
  }
}
```

```typescript
// web/src/types/index.ts
export interface FlashData {
  messages?: { level: string; message: string }[]
}

export interface SharedProps {
  auth: { user: { id: string; username: string; admin: boolean } | null }
}
```

**Convention:** Use `auth: { user: ... }` as the shared props key — this matches the
Django shared-prop contract (`auth={"user": user_summary}`).
The `auth` namespace separates authentication data from page props, preventing
collisions when a page has its own `user` prop. Do NOT use `current_user:` or
`user:` as top-level keys — they collide with page-specific props and break the
convention that other Inertia skills and examples assume.

## BAD vs GOOD Patterns

```tsx
// BAD — passing shared props as generics:
// usePage<{ users: User[], auth: AuthData, flash: FlashData }>()

// BAD — extending a SharedProps interface into page props:
// interface Props extends SharedData { users: User[] }

// BAD — declaring PageProps interface:
// interface PageProps { auth: AuthData; flash: FlashData }

// BAD — using current_user or user as top-level shared key:
// interface SharedProps { current_user: User }

// BAD — destructuring auth directly from usePage() (TS2339: 'auth' does not exist on Page):
// const { auth } = usePage()
// usePage() returns a Page object with { props, flash, component, url, ... }
// auth lives inside props, not on the Page itself

// BAD — duplicating InertiaConfig in index.ts (it belongs in globals.d.ts):
// declare module '@inertiajs/core' { ... }  ← in index.ts

// GOOD — props from usePage().props, flash from usePage().flash:
const { props, flash } = usePage()
// props.auth is typed (from SharedProps via InertiaConfig)
// flash.messages is typed (from FlashData via InertiaConfig)
```

**Important:** `globals.d.ts` configures InertiaConfig ONCE. When adding a new shared
prop, only update `index.ts` — do NOT touch `globals.d.ts`:

```typescript
// BEFORE — web/src/types/index.ts
export interface SharedProps {
  auth: { user: { id: string; username: string; admin: boolean } | null }
}

// AFTER — add the new key here, NOT in globals.d.ts
export interface SharedProps {
  auth: { user: { id: string; username: string; admin: boolean } | null }
  notifications: { unread_count: number }
}
```

InertiaConfig in `globals.d.ts` references `SharedProps` by name — it picks up the
change automatically. Adding a second `declare module '@inertiajs/core'` causes conflicts.

## Page-Specific Props

Page components type ONLY their own props. Shared props (like auth) and flash come from
InertiaConfig automatically.

### `type` vs `interface` for page props (React-specific)

This constraint applies to **React only**. Vue's `defineProps<T>()` and Svelte's
`$props()` do not use `usePage<T>()` generics, so `interface` works fine there.

`usePage<T>()` requires `T` to have an index signature. `type` aliases have one
implicitly; `interface` declarations do not. Using `interface` with `usePage`
causes TS2344 at compile time.

| Pattern | Works with `usePage<T>()`? | Notes |
|---------|---------------------------|-------|
| `type Props = { users: User[] }` | Yes | Preferred — just works |
| `interface Props { users: User[] }` | **No** — TS2344 | Missing index signature |
| `usePage<Required<Props>>()` | Yes | Wraps interface to add index signature |

```tsx
// React
type Props = {
  users: User[]         // page-specific only
  // auth is NOT here — it comes from InertiaConfig globally
}

export default function Index({ users }: Props) {
  // Access shared props separately:
  const { props, flash } = usePage()
  // props.auth is typed via InertiaConfig
  // flash.messages is typed via InertiaConfig
  return <UserList users={users} />
}
```

### Accessing shared props in Vue and Svelte

Vue and Svelte use different patterns to access shared props, but InertiaConfig
typing works the same way.

```vue
<!-- Vue 3 — usePage() returns reactive object; use computed() for derived values -->
<script setup lang="ts">
import { usePage } from '@inertiajs/vue3'
import { computed } from 'vue'

const page = usePage()
const userName = computed(() => page.props.auth.user?.name) // typed via InertiaConfig
</script>
```

```svelte
<!-- Svelte — page store from @inertiajs/svelte -->
<script lang="ts">
  import { page } from '@inertiajs/svelte'
  // $page.props.auth is typed via InertiaConfig
  // $page.flash.messages is typed via InertiaConfig
</script>
```

## Common TypeScript Errors

| Error | Cause | Fix |
|-------|-------|-----|
| **TS2344** on `usePage<Props>()` | `interface` lacks index signature | Use `type Props = { ... }` instead of `interface`, or wrap: `usePage<Required<Props>>()` |
| **TS2339** `'auth' does not exist on type Page` | Destructuring `auth` from `usePage()` directly | `usePage()` returns `{ props, flash, ... }` — use `usePage().props.auth`, not `usePage().auth` |
| **TS2339** `'flash' does not exist on type` | Accessing `usePage().props.flash` | Flash is top-level: `usePage().flash`, NOT `usePage().props.flash` |
| Shared props untyped | Missing InertiaConfig | Add `globals.d.ts` with module augmentation (see above) |
| InertiaConfig not taking effect | Declaration in wrong file | Must be in a `.d.ts` file (e.g., `globals.d.ts`), not in `.ts`; an included .ts module augmentation also works, as in web/src/types.ts |
| Types correct but IDE shows errors | `globals.d.ts` not included | Verify `tsconfig.app.json` includes the types directory in `include` array |

## Contract Updates

Update web/src/types.ts with the producer DTO and request tests. There is no
Typelizer generator. If a generator is introduced, document its actual inputs,
output and reproducible command.

## Related Skills
- **Shared props setup** → `inertia-python-controllers` (share(request, ...))
- **Flash config** → `inertia-python-controllers` (Django messages)
- **Explicit DTO contracts** → `python-serialization`
- **Page component props** → `inertia-python-pages` (type Props pattern)
