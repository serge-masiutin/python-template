---
name: python-boot-profiling
description: Profile Python and Django startup to separate interpreter and imports, Django setup, URL loading, database readiness and first-request work. Use for slow boot or readiness regressions, not ordinary request profiling.
---

## Project Context

Use Python and dependencies from mise.toml and uv.lock. Keep the target environment,
process model and filesystem cache conditions identical before and after a change.
Store profiles in tmp/; exclude secrets and private request data. Preserve config
validation and security checks. See docs/testing.md for the project test commands.

# Python Boot Time Profiling

Preserve the source boot-profiling workflow: establish a baseline, narrow slow
imports, inspect initialization and I/O, then verify a measured local fix.
Use Python importtime and cProfile rather than inventing require-profiler APIs.

## Prerequisites

1. Install locked dependencies with uv sync --frozen.
2. Select development or production settings and the same environment each run.
3. Load trusted local variables explicitly when needed: set -a; source .env; set +a.
4. Avoid autoreload and preloaded worker forks when measuring a fresh process.
5. Distinguish server boot from database readiness and the first HTTP request.

## Step 1: Run a Full Boot Profile

```sh
mkdir -p tmp
uv run --frozen python -X importtime -c 'from config.wsgi import application' 2>tmp/importtime.log
```

importtime reports self and cumulative import durations in microseconds. A module
with a high cumulative time may mostly import expensive children. Keep stderr
intact: real warnings and startup exceptions must not be hidden.
Measure process wall time separately; importing WSGI does not open every database
connection or execute all lazy URL and request logic.

## Step 2: Narrow the Scope

### Filter by Threshold

Retain the full profile. For a quick self-time view, inspect the importtime rows
with a threshold in microseconds. Do not sum cumulative times: they overlap.

```sh
awk -F '|' '/^import time:/ {if ($1 ~ /[0-9]/ && substr($1, 13) + 0 >= 100000) print}' tmp/importtime.log
```

### Filter by Focus Pattern

```sh
rg 'django|psycopg|inertia|accounts|notes' tmp/importtime.log
```

Filtering text does not preserve ancestors automatically. Reopen the full profile
to inspect the dependency chain. Do not confuse absence from this view with zero cost.

## Step 3: Check Configuration and HTTP Activity During Boot

importtime measures imports; it does not label YAML, SQL or HTTP automatically.
Inspect module-level code, AppConfig.ready(), settings loaders and URL imports.
Use existing structured timing/tracing or a narrow perf_counter measurement at
an identified boundary. Log durations and operation names, never secrets or bodies.
Do not execute a database query or remote call from AppConfig.ready merely to
measure it. Keep nonessential network setup out of application initialization.

## Step 4: Check Django Initialization Lines

Separate settings import, django.setup(), app registration and URL resolution.
The production WSGI import invokes Django setup. Importing config.urls or running
a first test request includes additional work; measure these as separate scenarios.
Compare fresh workers with the actual Gunicorn preload setting and worker count.

## Step 5: Deep-Dive with cProfile

```sh
uv run --frozen python -m cProfile -o tmp/boot.prof -m config.wsgi
uv run --frozen python -c 'import pstats; pstats.Stats("tmp/boot.prof").strip_dirs().sort_stats("cumulative").print_stats(30)'
```

Profile a known slow startup path before changing it. cProfile changes timing;
use uninstrumented repeated wall-time measurements to confirm improvements.
Inspect both self and cumulative time and identify the expensive callable.

## Step 6: Export a Profile for Handoff

Share the pstats artifact and sanitized commands, versions, environment, cache
conditions and measurements. pstats is not Speedscope JSON. If a sampling profiler
is already installed, use its documented export mode; do not claim cProfile emits
Speedscope or add a profiler without a specific diagnostic need.

## Collapsed Call Stack Format

Collapsed stacks require a compatible sampling profiler/exporter. Do not rename
importtime logs or .prof files to manufacture that format. Keep the original
measurement artifact alongside any verified conversion.

## Configuration Reference

| Setting | Purpose |
|---|---|
| -X importtime | Import timings to stderr |
| PYTHONPROFILEIMPORTTIME=1 | Environment equivalent for child processes |
| DJANGO_SETTINGS_MODULE | Explicit settings module |
| APP_ENV | Starter environment; do not compare different modes |
| Gunicorn preload / workers | Record the actual process model |

## Important: Preserve Measurement Context

Filter only a saved copy/view of the complete baseline. Avoid suppressing stderr,
silently skipping failed starts, or comparing instrumented and uninstrumented runs.
Lazy imports move work to first use: measure the affected first request as well.

## Recommended Agent Workflow

1. Read manifests, settings, WSGI/ASGI entrypoint and deployment command.
2. Record several comparable fresh-process wall-time measurements.
3. Run one importtime profile and inspect the largest self/cumulative contributors.
4. Inspect the identified module and configuration/network work it triggers.
5. Use cProfile only for the slow path that needs deeper explanation.
6. Preserve sanitized artifacts and identify measured facts versus hypotheses.
7. Make the smallest justified fix: remove unused startup imports, move optional
   initialization to an explicit boundary, or correct eager configuration work.
   Do not disable validation, introduce hidden caches or defer failures merely to
   make boot appear faster. Rerun the focused profile and comparable full startup
   and first-request measurements before reporting an improvement.
