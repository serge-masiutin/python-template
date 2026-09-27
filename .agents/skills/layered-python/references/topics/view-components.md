# View Components

## Contents

- Summary
- Layer Placement
- When to Use
- When NOT to Use
- Key Principles
- Implementation
- Testing Components
- Common Component Patterns
- When to Extract a Component
- Anti-Patterns
- File Organization

## Summary

React components encapsulate view logic, replacing complex page markup with testable, reusable units. They bridge the presentation layer's need for logic with explicit typed props.

## Layer Placement

```
┌─────────────────────────────────────────┐
│ Presentation Layer                      │
│  ├─ Views (ERB/HTML)                    │
│  ├─ React components (logic + template)   │
│  └─ Presenters (view-specific logic)    │
└─────────────────────────────────────────┘
```

## When to Use

- Partials with complex logic
- Reusable UI elements across views
- Components needing isolated testing
- Preview/documentation requirements

## When NOT to Use

- Simple static markup (use partials)
- One-off display logic (use helpers)
- Data transformation (use presenters/serializers)

## Key Principles

- **Single responsibility** — one component, one purpose
- **Explicit interface** — typed inputs, no magic
- **Isolated testing** — unit test without full request
- **Composition** — build complex UIs from simple components

## Implementation

### Basic Component

```tsx
type AvatarProps = { name: string; src: string | null; size: "small" | "medium" | "large" };
function Avatar({ name, src, size }: AvatarProps) {
  const sizes = { small: "size-8", medium: "size-16", large: "size-32" };
  const initials = name.split(/\s+/).map(part => part[0]).join("").slice(0, 2).toUpperCase();
  return src ? <img src={src} alt={name} className={sizes[size]} />
    : <span aria-label={name} className={sizes[size]}>{initials}</span>;
}
```

### Component with Template

```tsx
type CardProps = { header?: React.ReactNode; footer?: React.ReactNode;
  actions?: React.ReactNode; children: React.ReactNode };
```

```tsx
function Card({ header, footer, actions, children }: CardProps) {
  return <article>{header && <header>{header}</header>}<div>{children}</div>
    {actions && <div>{actions}</div>}{footer && <footer>{footer}</footer>}</article>;
}
```

### Usage in Views

```tsx
<Card header="Post details" footer={post.publishedAt}
  actions={<><Link href={post.url}>Read more</Link><SharePost postId={post.id} /></>}>
  <h2>{post.title}</h2><p>{post.excerpt}</p>
</Card>
```

### Component with Slots and Polymorphism

```tsx
type NoticeProps = { tone: "info" | "success" | "warning" | "error"; children: React.ReactNode };
function Notice({ tone, children }: NoticeProps) {
  return <div role={tone === "error" ? "alert" : "status"} data-tone={tone}>{children}</div>;
}
```

### Component Composition

```tsx
type PostListProps = { posts: PostSummary[] };
```

```tsx
function PostList({ posts }: PostListProps) {
  return <div>{posts.map(post => <PostCard key={post.id} post={post} />)}</div>;
}
```

## Testing Components

```tsx
it("renders initials when no image is supplied", () => {
  render(<Avatar name="John Doe" src={null} size="small" />);
  expect(screen.getByLabelText("John Doe")).toHaveTextContent("JD");
});
```

### Preview Components

```tsx
const meta = { title: "Components/Avatar", component: Avatar,
  args: { name: "Preview User", src: null, size: "medium" },
  argTypes: { size: { control: "select", options: ["small", "medium", "large"] } }
  satisfies Meta<typeof Avatar>;
export default meta;
export const WithoutImage: StoryObj<typeof meta> = {};
export const Large: StoryObj<typeof meta> = { args: { size: "large" } };
```

## Common Component Patterns

### Collection Component

```tsx
<PostList posts={posts} />
```

### Inline Component

```tsx
const labels = { draft: "Draft", published: "Published", archived: "Archived" };
function StatusBadge({ status }: { status: keyof typeof labels }) {
  return <span data-status={status}>{labels[status]}</span>;
}
```

### Stimulus Integration

```tsx
type DisclosureProps = { label: string; children: React.ReactNode };
```

```tsx
function Disclosure({ label, children }: DisclosureProps) {
  return <details><summary>{label}</summary><div>{children}</div></details>;
}
```

## When to Extract a Component

### From Helpers

Extract helpers to React components when you see:

| Signal | Example | Action |
|--------|---------|--------|
| Heavy `tag.*` usage | `tag.div`, `tag.button` chains | Extract to component with template |
| Complex data attributes | `data: { controller: ..., action: ... }` | Component encapsulates Stimulus wiring |
| Conditional CSS classes | `class: "foo #{bar if baz}"` | Component method for class logic |
| Nested structure | Helper yielding to blocks with wrappers | Component with slots |
| Error handling in render | `rescue` in helper methods | Component with proper error boundaries |

**Before (Helper):**
```python
# Bad: server helpers generate the React component's structure.
markup = format_html('<div id="message-area">{}</div>', message.body)
```

**After (React component):**
```tsx
type MessageAreaProps = { roomId: string; children: React.ReactNode };
```

```tsx
function MessageArea({ roomId, children }: MessageAreaProps) {
  return <section aria-label="Messages" data-room-id={roomId}>{children}</section>;
}
// A dedicated hook owns any subscription and disconnects it on cleanup.
```

### From Presenters

Extract presenters to React components when:
- Presenter has a `render` method returning HTML
- Presenter accepts `context: self` for helper access
- Presenter builds complex markup via `content_tag` or `tag.*`

**Signal:** `Presenter(record, request).render()`

This pattern indicates the presenter is doing component work without component benefits.

## Anti-Patterns

### Data Fetching in Components

```tsx
function RecentPosts({ posts }: { posts: PostSummary[] }) {
  return <PostList posts={posts} />;
}
// Page props come from the server; no second useEffect/fetch lifecycle.
```

### Business Logic in Components

```tsx
function PostActions({ post }: { post: PostActionsProps }) {
  return <div>{post.canUpdate && <Link href={post.editUrl}>Edit</Link>}
    {post.canDelete && <DeletePost postId={post.id} />}</div>;
}
// The server still enforces both actions.
```

### God Components

```tsx
<><PostHeader post={post} /><PostBody post={post} />
<PostActions post={post} /><CommentsList comments={comments} /></>
```

## File Organization

```
web/components/
├── Layout.tsx
├── Notice.tsx
├── alert_component.tsx
├── Card.tsx
├── card_component.tsx
├── posts/
│   ├── Card.tsx
│   ├── card_component.tsx
│   ├── List.tsx
│   └── list_component.tsx
└── users/
    ├── Avatar.tsx
    └── profile_Card.tsx
```
