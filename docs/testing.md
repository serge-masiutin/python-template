# Testing

Install with mise install, uv sync --frozen and npm ci. Run from the root:

```sh
mise exec -- bin/ci
```

bin/ci checks Ruff, Django settings/migration drift, pytest contracts, TypeScript,
Vitest, Vite and Storybook builds, design contracts, skill hashes/mappings and links.
It uses an in-memory SQLite test database by default.

## PostgreSQL

Start docker compose up -d --wait db, then run:

```sh
TEST_POSTGRES=1 mise exec -- uv run --frozen pytest
```

Django creates and destroys test_starter; the configured account needs CREATEDB.
Override DATABASE_URL only with a disposable test instance. The same suite runs
against PostgreSQL in GitHub Actions. This catches database behavior that SQLite
cannot establish.

## Browser and Storybook

```sh
mise exec -- npx playwright install chromium
mise exec -- npm run test:browser
mise exec -- npm run test:storybook
```

Application flows use config.settings_browser and tmp/browser.sqlite3, synthetic
accounts, built assets and port 8100. The preparation script resets only its own
fixture users' notes. Production settings are never used by this script.
Storybook browser tests run colocated play functions and accessibility checks.
Builds alone do not execute them.

## Skills

scripts/check-skills.mjs checks inventories, pinned bytes, archives, patches,
frontmatter, adapted local links and code fences. scripts/check-skill-sources.py
also verifies original archive members, complete mappings and Python snippet syntax.
The latter is a structural check, not a model-quality benchmark. docs/skill-evals.md
records task-based review cases and which are exercised by runtime tests.

Review a skill diff before running scripts/update-skill-lock.py. Never refresh
upstream hashes to hide drift. See skills.md for provenance and update boundaries.
