# Prop Types — Detailed Reference

Each prop type with real-world examples for inertia-rails 3.17+.

## Table of Contents

- [Regular Props](#regular-props)
- [Optional Props](#optional-props)
- [Deferred Props](#deferred-props)
- [Once Props](#once-props)
- [Merge Props](#merge-props)
- [Always Props](#always-props)
- [Scroll Props](#scroll-props)
- [Resetting Merge/Scroll Props](#resetting-mergescroll-props)
- [Combining Prop Types](#combining-prop-types)
---

## Regular Props

Always included in the initial page response. Wrap in `-> {}` to skip evaluation during partial reloads that don't request them.

```python
return render(request, "Users/Index", props={
    "filters": validated_filters,
    "users": lambda: [user_summary(user) for user in active_users],
    "total_count": lambda: active_users.count(),
})
```

With `router.reload({ only: ['filters'] })`, `users` and `total_count` are never evaluated.

Rule of thumb: wrap anything involving a query in `-> {}`. Use plain values only for cheap data like params or literals.

## Optional Props

Only evaluated when explicitly requested via partial reload headers.
Saves computation on initial page load.

```python
return render(request, "Users/Index", props={
    "users": [user_summary(user) for user in active_users],
    "detailed_stats": optional(lambda: detailed_stats(actor=request.user)),
})
# Stream CSV through a separate authorized download endpoint, not a page prop.
```

Client requests optional props with `router.reload`:
```tsx
// Only fetches export_data, skips everything else
router.reload({ only: ['export_data'] })
```

## Deferred Props

Loaded automatically after the initial page render. The page loads fast
with a placeholder, then deferred data streams in.

```python
return render(request, "Courses/Show", props={
    "course": course_summary(course),
    "reviews": defer(lambda: review_summaries(course.reviews.select_related("user"))),
    "chart_data": defer(lambda: chart_for(course), group="analytics"),
    "engagement": defer(lambda: engagement_for(course), group="analytics"),
})
```

React side with `<Deferred>`:
```tsx
<Deferred data="reviews" fallback={<ReviewsSkeleton />}>
  <ReviewsList />
</Deferred>
```

## Once Props

Resolved once per session, remembered across navigations.
Use for reference data that rarely changes.

```python
return render(request, "Courses/Index", props={
    "countries": once(lambda: list(Country.objects.values("name", "code"))),
    "timezones": once(lambda: sorted(available_timezones())),
})
# Do not cache access decisions with once; always reauthorize at the server.
```

## Merge Props

Appended to existing array on the client. Use for accumulating data across
partial reloads — new items are added to the existing list without replacing it.

When merging arrays, you may use the `match_on` parameter to match existing items
by a specific field and update them instead of appending new ones.

For **infinite scroll**, prefer `scroll` (see [Scroll Props](#scroll-props))
which handles scroll-aware loading automatically. Use `merge` for patterns where
data accumulates from user actions or background updates:

```python
return render(request, "Feed", props={
    "messages": merge(lambda: message_summaries(messages_scope), match_on="id"),
    "posts": merge(lambda: post_page(), append="data", match_on="data.id"),
})
# merge/deep_merge only affect partial reloads. Use stable IDs and bounded windows.
```

Client-side, `router.reload({ only: ['messages'] })` fetches the new batch
and Inertia appends it to the existing `messages` array automatically.

**Reset on fresh visit:** Merge only appends during partial reloads. A full
page visit (navigation, `router.get`) replaces the prop entirely — no stale
accumulation across pages.

## Always Props

Included even in partial reloads (which normally only include
requested props). Use sparingly for data that must always be fresh.

```python
return render(request, "Users/Index", props={
    "users": lambda: user_summaries(users_scope),
    "csrfToken": always(lambda: get_token(request)),
})
```

## Scroll Props

Scroll-aware props for infinite scroll. Combines with `<InfiniteScroll>` on the
client to automatically load more data as the user scrolls down.

Use django.core.paginator.Paginator and the installed scroll signature.

```python
from django.core.paginator import Paginator
page = Paginator(posts_scope.order_by("-created_at", "-pk"), 20).get_page(request.GET.get("page", 1))
return render(request, "Posts/Index", props={
    "posts": scroll(
        lambda: [post_summary(post) for post in page.object_list],
        {"pageName": "page", "currentPage": page.number,
         "previousPage": page.previous_page_number() if page.has_previous() else None,
         "nextPage": page.next_page_number() if page.has_next() else None},
    ),
})
```

React side with `<InfiniteScroll>`:
```tsx
import { InfiniteScroll } from '@inertiajs/react'

export default function Index({ posts }: Props) {
  return (
    <InfiniteScroll data="posts" loading={() => <PostsSkeleton />}>
      {posts.map(post => <PostCard key={post.id} post={post} />)}
    </InfiniteScroll>
  )
}

// Manual mode — "Load more" button instead of auto-scroll
export function IndexManual({ posts }: Props) {
  return (
    <InfiniteScroll
      data="posts"
      manual
      next={({ loading, fetch, hasMore }) =>
        hasMore && (
          <button onClick={fetch} disabled={loading}>
            {loading ? 'Loading...' : 'Load more'}
          </button>
        )
      }
    >
      {posts.map(post => <PostCard key={post.id} post={post} />)}
    </InfiniteScroll>
  )
}
```

**NEVER use `<WhenVisible>` for infinite scroll** — use `<InfiniteScroll>` which
handles page tracking, URL sync, and merge behavior automatically.

## Resetting Merge/Scroll Props

Merge and scroll props accumulate data across partial reloads. To discard the
accumulated state and start fresh **without a full page visit**, pass `reset`
on the client:

```tsx
// Fetch messages from scratch — clears the accumulated array first
router.reload({ only: ['messages'], reset: ['messages'] })
```

**Use when user changes filters / sort order: `reset` the prop so stale items are discarded.**

## Combining Prop Types

Prop helpers accept keyword arguments that layer behaviours together:

```python
return render(request, "Feed", props={
    "posts": defer(lambda: post_summaries(posts_scope), group="feed", merge=True, match_on="id"),
    "comments": defer(lambda: comment_summaries(comments_scope), group="feed", merge=True, match_on="id"),
})
# optional() accepts once options, not merge=True. Do not invent that combination.
```

The `merge: true` flag works on `defer`, `optional`, and `always`. It tells
Inertia to append results to the existing client-side array on partial reloads
instead of replacing it — the same behaviour as `merge`, but
combined with another prop type.
