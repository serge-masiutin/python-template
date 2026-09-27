---
name: inertia-python-architecture
description: >-
  Server-driven architecture patterns for Inertia Django + React. Load this FIRST when building any Inertia page
  or feature — it routes to the right skill. Decision matrix for data loading, forms, navigation, state management.
  NEVER useEffect+fetch, NEVER redirect for external URLs (use location), NEVER react-hook-form
  (use Form component). MUST invoke when adding pages, models with views, CRUD, or displaying data in an
  Inertia Django app. ALWAYS `render(request, "Page", props={"key": value})` to pass data — `@ivars` are NOT auto-passed as props.
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


# Inertia Django Architecture

Server-driven architecture for Django + Inertia.js + React when building pages,
forms, navigation, or data refresh. Inertia is NOT a traditional SPA — the
server owns routing, data, and auth. React handles rendering only.

## The Core Mental Model

The server is the source of truth. React receives data as props and renders UI.
There is no client-side router, no global state store, no API layer.

**Before building any feature, ask:**
- **Where does the data come from?** → If server: controller prop. If user interaction: `useState`.
- **Who owns this state?** → If it's in the URL or DB: server owns it (use props). If it's ephemeral UI: React owns it.
- **Am I reaching for a React/SPA pattern?** → Check the decision matrix below first — Inertia likely has a server-driven equivalent.

## Decision Matrix

| Need | Solution | NOT This |
|------|----------|----------|
| Page data from server | Controller props | useEffect + fetch |
| Global data (auth, config) | `share(request, ...)` + `usePage()` | React Context / Redux |
| Flash messages / toasts | Django messages + `usePage().flash` | share(request, ...) / React state |
| Form submission | `<Form>` component | fetch/axios + useState |
| Navigate between pages | `<Link>` / `router.visit` | react-router / window.location |
| Refresh specific data | `router.reload({ only: [...] })` | React Query / SWR |
| Expensive server data | `defer` | useEffect + loading state |
| Infinite scroll | `scroll` + `<InfiniteScroll>` | Client-side pagination |
| Stable reference data | `once` | Cache in React state |
| Real-time updates (core) | a configured realtime adapter + `router.reload` | Polling with setInterval |
| Simple polling (MVP/prototyping) | `usePoll` (auto-throttles in background tabs) | setInterval + router.reload |
| URL-driven UI state (dialogs, tabs) | Controller reads `params` → prop, `router.get` to update | useEffect + window.location |
| Ephemeral UI state | `useState` / `useReducer` | Server props |
| External API calls | Dedicated API endpoint | Mixing with Inertia props |

## Rules (by impact)

| # | Impact | Rule | WHY |
|---|--------|------|-----|
| 1 | CRITICAL | Never useEffect+fetch for page data | Inertia re-renders the full component on navigation; a useEffect fetch creates a second data lifecycle that drifts from props and causes stale UI |
| 2 | CRITICAL | Never check auth client-side | Auth state in React can be spoofed; server-side checks are the only real gate. Client-side "guards" give false security |
| 3 | CRITICAL | Use `<Form>`, not fetch/axios | `<Form>` handles CSRF, redirect-following, error mapping, file detection, and history state — fetch duplicates or breaks all of this |
| 4 | HIGH | Use `<Link>` and `router`, not `<a>` or window.location | `<a>` triggers a full page reload, destroying all React state and layout persistence |
| 5 | HIGH | Use partial reloads, not React Query/SWR | React Query adds a second cache layer that conflicts with Inertia's page-based caching and versioning |
| 5b | HIGH | Use `usePoll` only for MVPs; prefer a configured realtime adapter for production real-time | `usePoll` is convenient but wastes bandwidth — every interval hits the server even when nothing changed. a configured realtime adapter pushes only on actual changes |
| 6 | HIGH | Use `share(request, ...)` for global data, not React Context | Context re-renders consumers on every change; shared props are per-request and integrated with partial reloads |
| 7 | HIGH | Use Django messages for notifications, not shared props | Flash auto-clears after one response; shared props persist until explicitly changed, causing stale toasts |
| 8 | MEDIUM | Use deferred/optional props for expensive queries | Blocks initial render otherwise — user sees blank page until slow query finishes |
| 9 | MEDIUM | Use persistent layouts for state preservation | Without persistent layout, layout remounts on every navigation — scroll position, audio playback, and component state are lost |
| 10 | MEDIUM | Keep React components as renderers, not data fetchers | Mixing data-fetching into components makes them untestable and breaks Inertia's server-driven model |

## Skill Map

Common workflows span multiple skills — load all listed for complete coverage:

| Workflow | Load these skills |
|----------|-------------------|
| New page with props | `inertia-python-controllers` + `inertia-python-pages` + `inertia-python-typescript` |
| Form with validation | `inertia-python-forms` + `inertia-python-controllers` |
| shadcn form inputs | `inertia-python-forms` + `shadcn-inertia` |
| Flash toasts | `inertia-python-controllers` + `inertia-python-pages` + `shadcn-inertia` |
| Deferred/lazy data | `inertia-python-controllers` + `inertia-python-pages` |
| URL-driven dialog/tabs | `inertia-python-controllers` + `inertia-python-pages` |
| Alba serialization | `python-serialization` + `inertia-python-typescript` |
| Testing controllers | `inertia-python-testing` + `inertia-python-controllers` |

## References

**MANDATORY — READ ENTIRE FILE** before building a new Inertia page or feature:
[`references/AGENTS.md`](references/AGENTS.md) (~430 lines) — full-stack examples for
each pattern in the decision matrix above.

**MANDATORY — READ ENTIRE FILE** when unsure which Inertia pattern to use:
[`references/decision-trees.md`](references/decision-trees.md) (~70 lines) — flowcharts
for choosing between prop types, navigation methods, and data strategies.

**Do NOT load** references for quick questions about a single pattern already
covered in the decision matrix above.

## When You DO Need a Separate API

Not everything belongs in Inertia's request cycle. Use a traditional API endpoint when:

| Signal | Why | Example |
|--------|-----|---------|
| Non-browser consumer | Inertia's JSON envelope (component, props, url, version) is designed for the frontend adapter — other consumers can't use it | Mobile API, CLI tools, payment webhooks |
| Large-dataset search | Dataset is too big to load as a prop; each input needs per-keystroke server filtering. Use raw fetch for the search, let Inertia handle post-selection side effects via props. | City/address autocomplete, postal code lookup |
| Binary/streaming response | Inertia can only deliver JSON props. Use a separate route with a standard download response. | PDF/CSV export, file downloads |
