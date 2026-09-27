# Development

Use the checked-in mise versions. `bin/setup` installs frozen uv/npm dependencies,
starts PostgreSQL with Compose, builds frontend assets and runs migrations. `.env`
is a trusted shell file sourced by bin/manage; never source an untrusted download.

## Configuration

.env.example documents local variables. SECRET_KEY must contain at least 32 characters;
ALLOWED_HOSTS must list explicit hosts; DATABASE_URL must be a PostgreSQL URI without
query or fragment. Production requires ASSET_VERSION and enables secure cookies,
HTTPS redirects and HSTS. Do not expose the development server publicly.

## Users and migrations

Run `mise exec -- bin/manage createsuperuser`; Django prompts without displaying
the password. Use admin to create ordinary users and assign explicit permissions.
The custom accounts.User model exists from the initial migration. For a model change,
run bin/manage makemigrations, inspect it, then bin/manage migrate and relevant tests.
Model save does not invoke full_clean; forms validate browser input and DB constraints
protect concurrent invariants.

## Frontend and catalog

bin/dev runs Vite on 127.0.0.1:5173 and Django on 127.0.0.1:8000. Visit the latter.
Django-vite resolves development modules; production reads web/build/manifest.json.
Use npm run storybook for the independent catalog. Components and stories live in
web/src/components. DESIGN.md documents reuse and contract verification.

## GitHub

A generated project should configure its own repository-local identity and remote.
No author credentials, machine paths or global Git/SSH configuration are bundled.
