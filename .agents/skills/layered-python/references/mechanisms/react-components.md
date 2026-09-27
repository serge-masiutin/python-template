# React Components and Storybook

Adaptation of React component's public inputs, slots, collections, previews and testing.
For this template, React is the presentation layer and Storybook supplies previews.
Use the original `sb-*`, `design-system` and `tailwind-best-practices` skills.

## Installation and Basic Usage

React, TypeScript, Vite and Storybook are installed. Read package versions and real
components before adding a dependency. Public component contracts and tokens are
linked from the root `DESIGN.md`.

```tsx
type AvatarProps = { src: string; name: string; size: "small" | "large" };
function Avatar({ src, name, size }: AvatarProps) {
  const dimensions = { small: "size-8", large: "size-12" };
  return <img src={src} alt={name} className={`rounded-full ${dimensions[size]}`} />;
}
```

Use fixed variants. A public arbitrary `className` escape hatch can undermine the
contract's visual promises.

## Slots

Use `children` for the primary body and named `ReactNode` props for truly distinct
optional regions. Define required regions, order, accessible labels and who owns
layout. Do not duplicate a component to change one slot.

## Collections

Render real components with stable domain keys. Keep data loading and authorization
on the server; components receive public props. Do not pass ORM-shaped unfiltered
records or invent an extra API just to feed a page.

## Inline Components and Interaction

A small local component can stay beside its consumer until it has a stable reusable
role. React owns local state, focus and event handling; Stimulus is not installed.
Inertia owns navigation and form requests. Clean up subscriptions in effects.

## Previews

Keep the established colocated Storybook location. Import the production component,
use deterministic fixtures and cover materially distinct states: invalid, disabled,
empty, long content, narrow width and keyboard interaction where applicable.
Expose enum controls and hide callbacks from Controls. Do not re-author page markup
inside a story or connect preview controls to live services.

## Testing

Use Vitest/Testing Library for public interaction contracts, Storybook browser tests
for component rendering/accessibility and Playwright for the real Inertia flow.
A successful build does not prove keyboard behavior or that application CSS loaded.
Keep one CSS evidence story and inspect the actual rendered result.
