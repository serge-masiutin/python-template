# Loading Options at the Django Boundary

Import helpers from inertia; check the installed version before changing options.

| Loading requirement | Implementation | Contract |
|---|---|---|
| Regular | Explicit DTO value | Authorized bounded shape |
| Lazy | lambda returning safe props | Evaluated only if selected |
| Optional | optional(lambda: values()) | Explicit partial request only |
| Deferred | defer(lambda: values()) | Initial loading state and later request |
| Deferred group | defer(..., group="analytics") | Grouped request; no cross-user sharing |
| Once | once(lambda: values()) | Client reuse; not an authorization boundary |
| Once with expiry | once(..., expires_at=60) | Seconds or datetime/timedelta in this adapter |
| Always | always(lambda: value()) | Required even on partial reloads |
| Merge | merge(..., match_on="id") | Stable IDs and bounded partial accumulation |
| Deep merge | deep_merge(lambda: payload()) | Explicit nested contract |
| Scroll | scroll(lambda: rows(), metadata) | pageName/currentPage/previousPage/nextPage |
| Reset | router.reload({reset: ["rows"]}) | Clear accumulated rows when filters change |

## Combining Options

Django defer accepts group, merge, deep_merge and match_on; optional accepts once
options but not merge=True. A DTO does not own any of these flags. Authorize on
every deferred/partial request and before every query.

Keep cache keys scoped by access, tenant, version and locale where relevant.
History encryption and client once reuse do not revoke already exposed data.
Long provider calls belong in explicit operations, with a configured worker and
persisted state if needed. This starter installs no queue, realtime or AI backend.
