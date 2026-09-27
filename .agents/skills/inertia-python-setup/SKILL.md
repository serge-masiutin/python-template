---
name: inertia-python-setup
description: Detect and align Django, inertia-django, React, TypeScript, Vite, PostgreSQL and Storybook when bootstrapping or changing this starter. Preserve configured dependencies and add only missing capabilities required by the task.
---

# Inertia Django Project Setup

Detect the existing stack, fill concrete gaps, update the repository contract.
Run once per project and after a deliberate stack change.

**Never** overwrite configuration before reading it, infer installed APIs from Rails
examples, or add dependencies merely because a catalog recommends them.

## Step 1: Detect Current Stack

Read pyproject.toml, uv.lock, package.json, package-lock.json, config/settings.py,
config/urls.py, web/src/app.tsx, vite.config.ts, tsconfig files and .storybook.

| Look for | Means |
|---|---|
| Django and inertia-django | Backend and Inertia protocol adapter |
| django-vite | Django template tags and Vite manifest integration |
| @inertiajs/react, vue3 or svelte | Actual frontend adapter; this starter uses React |
| django.contrib.auth and accounts.User | Session authentication and custom user model |
| PostgreSQL / psycopg | Production database contract |
| pytest-django | Request and model tests |
| components.json | shadcn configuration only if actually present |
| Storybook scripts and stories | Existing component preview conventions |

## Step 2: Recommend Missing Deps

Compare the requested feature to installed capabilities. Django already supplies
forms, auth, pagination and ORM queries. Explicit DTOs and TypeScript interfaces
need no serializer/codegen dependency. Reuse existing React components and contracts.
Recommend shadcn, a queue or an SDK only when a specific feature needs it; explain
its concrete contract and installation impact. Do not replace a chosen alternative.

## Step 3: Install Opted-In Deps

Use uv and npm with the checked-in versions and lockfiles. For an authorized
feature, add only the required package, update its lockfile and configure it explicitly.
Verify middleware order, CSRF/body parsing, URL trailing slashes, migrations and
safe JSON encoding. Keep Vite and TypeScript aliases consistent; no Ruby plugin
supplies aliases. Uploads need request.FILES, limits and storage policy.

## Step 4: Update the Repository Contract

Read [configuration blocks](references/claude-md-templates.md). Update the existing
AGENTS.md stack section locally; if a project already uses CLAUDE.md, preserve its
custom rules and link to one source of truth. Do not create competing instructions.
Document actual render, error, message and test contracts, not uninstalled generators.

## Troubleshooting

| Symptom | Cause to inspect | Fix |
|---|---|---|
| Vite manifest missing | Frontend not built | Run the configured npm build |
| Blank component | Name mismatch | Match render component to app.tsx resolver |
| CSRF 403 | Header, cookie or trusted origin mismatch | Use shared csrfToken and inspect Django settings |
| Form has no values | JSON/multipart method parsing | Use explicit form_input or request.FILES boundary |
| Private fields in JSON | Implicit model encoding | Keep DjangoJSONEncoder and explicit DTOs |
| Conflicting agent rules | Multiple stack blocks | Preserve one source and fix links |

## Step 5: Summary

Report changes, installed versions, relevant skills, verified commands and remaining
limits. Run the project's existing checks before declaring setup complete.
