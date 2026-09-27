# Deployment

Build with docker build -t python-template . The image serves Gunicorn on port 8000
as an unprivileged user and includes Vite assets plus collected Django admin static
files. It does not run migrations automatically in competing server workers.

## Required environment

APP_ENV=production, SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL and ASSET_VERSION are
required. Use a distinct random runtime secret, an explicit public hostname and a
release identifier that changes with assets. PostgreSQL credentials are deployment
secrets. The URI accepts no query options; configure TLS options explicitly in
settings for your provider, then test that connection.

## Release

```sh
docker run --rm --env-file .env.production python-template .venv/bin/python manage.py migrate
docker run --rm --env-file .env.production python-template .venv/bin/python manage.py check --deploy
docker run --env-file .env.production -p 127.0.0.1:8000:8000 python-template
```

These are deployment examples; provision the PostgreSQL instance and trusted HTTPS
reverse proxy for your environment. Keep the app port private. The proxy must replace
X-Forwarded-Proto rather than forwarding an untrusted client header. Secure cookies,
SSL redirects and HSTS assume HTTPS. For direct HTTP health probes behind the private
proxy, send the trusted forwarded scheme or probe through HTTPS.

GET /health/ performs SELECT 1 and fails if the database is unavailable. Supervise
the process, collect stderr logs and back up PostgreSQL. Configure log retention and
avoid request-body/query-string logging of private input. Run migrations before
traffic reaches a new release; review compatibility and backup/rollback separately.

No email, worker, AI provider or upload storage is installed. Add and configure those
as explicit features rather than treating skill examples as deployed infrastructure.
