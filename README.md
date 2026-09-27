# Python Template

A Django + Inertia + React starter with private notes, session authentication and Django admin. It carries the architecture and agent guidance from [rails-template](https://github.com/serge-masiutin/rails-template) into Python, while restoring the original Evil Martians React and Storybook skills.

- **Django backend:** PostgreSQL, migrations, custom user model, forms and explicit access checks.
- **React frontend:** TypeScript, Vite, Tailwind, local Martian Mono and Storybook.
- **32 agent skills:** original upstream files or traceable adaptations, with source archives, file mappings, hashes and patches.
- **Checks:** backend contracts, frontend tests, browser flows, Storybook accessibility and container builds.

[Quick start](#quick-start) · [How it works](#how-it-works) · [Documentation](#documentation)

## Quick start

Install Git, [mise](https://mise.jdx.dev/) and Docker with Compose. Use **Use this template** on GitHub, then clone your new repository:

```sh
git clone git@github.com:YOUR_ACCOUNT/YOUR_APP.git
cd YOUR_APP
mise trust
mise install
mise exec -- bin/setup
mise exec -- bin/manage createsuperuser
mise exec -- bin/dev
```

Open **http://127.0.0.1:8000**, sign in with the username and password you created, and add a note. The administrator can open Django admin to manage users and notes.

`bin/setup` creates a private `.env` with a random secret, installs locked dependencies, starts PostgreSQL on `127.0.0.1:5438`, builds assets and applies migrations. Re-running it preserves existing configuration and database data. Dependency and Docker downloads require network access.

Start the component catalog separately:

```sh
mise exec -- npm run storybook
```

Storybook runs at **http://localhost:6006**. Stories use synthetic props and do not call the application.

## How it works

```text
React Form → POST /notes/ → CSRF + input validation + authenticated owner
           → save note → 303 redirect → GET / → explicit Inertia props
```

Django serves the initial HTML and subsequent Inertia page responses. React has no separate page router or data-fetching layer. Queries and deletion are owner-scoped; IDs are strings in the browser contract. Public DTOs never include arbitrary model fields.

The starter keeps simple behavior in cohesive `accounts` and `notes` apps. `layered-python` retains the source skill’s four-layer model, pattern catalog, examples and audit workflows, with Django/Python mechanisms replacing Ruby-specific APIs.

## Development commands

| Command | Purpose |
|---|---|
| `mise exec -- bin/dev` | Django development server and Vite HMR |
| `mise exec -- bin/manage migrate` | Apply migrations |
| `mise exec -- bin/manage createsuperuser` | Create an administrator interactively |
| `mise exec -- bin/ci` | Lint, tests, builds and skill/design integrity |
| `mise exec -- npm run test:browser` | Isolated application browser flows |
| `mise exec -- npm run test:storybook` | Story interactions and accessibility |
| `docker build -t python-template .` | Production Gunicorn image |

Install Chromium before browser checks: `mise exec -- npx playwright install chromium`.
See [testing](docs/testing.md) for PostgreSQL and CI prerequisites.

## Scope

Implemented: private notes, sign-in/sign-out, validation, session/CSRF security, admin, asset integration and a component catalog. Background jobs, email delivery, AI, public registration, password recovery, uploads and realtime are extension points; they are not preinstalled features. Skills discuss their architecture without claiming those adapters are present.

## Documentation

- [Development](docs/development.md): setup, configuration, users and tools.
- [Architecture](docs/architecture.md): boundaries, routes, persistence and browser contracts.
- [Testing](docs/testing.md): backend, PostgreSQL, browser, Storybook and skill checks.
- [Deployment](docs/deployment.md): image, HTTPS, migrations and readiness.
- [Agent skills](docs/skills.md): catalog, origins, adaptation mappings and updates.
- [Design](DESIGN.md): components, tokens, contracts and previews.

## License

Application code is [MIT](LICENSE). Source attribution and bundled third-party licenses are in [THIRD_PARTY.md](THIRD_PARTY.md).
