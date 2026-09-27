# Repository Stack Blocks

Select only the blocks supported by inspected manifests and code. Update existing
instructions; do not append a second conflicting contract.

## Framework

Django views return inertia.render(request, explicit_component, props=...). React
owns ephemeral UI; Django owns URLs, authorization and persisted state.

## Serialization

Use bounded explicit DTO functions. DjangoJSONEncoder must not receive model
instances. Producer and consumer types change together; no type generator is installed.

## UI

Reuse web/src/components and design-system contracts. Preserve configured Storybook
story locations. Only use shadcn components if installed for the feature.

## Pagination

Use Django Paginator or an explicit stable cursor. Inertia scroll() takes props and
metadata; always scope by the current authorized actor before pagination.

## Testing

pytest-django and Django Client exercise actual middleware. Assert response JSON,
CSRF, ownership, 303 redirects, one-use errors/messages and partial loading.

## Routing

config/urls.py owns URLs. The starter has no automatic TypeScript route generator.
Use trailing slashes and update callers with server routes.

## Authorization

Authenticate at entrypoints, scope object lookups and repeat permission checks on
mutations. Frontend can props affect presentation, never authority.
