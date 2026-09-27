FROM node:24.21.0-bookworm-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY tsconfig.json vite.config.ts ./
COPY web ./web
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.12.19 AS uv
FROM python:3.14.7-slim-bookworm AS runtime
COPY --from=uv /uv /uvx /usr/local/bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY manage.py ./
COPY config ./config
COPY accounts ./accounts
COPY notes ./notes
COPY templates ./templates
COPY --from=frontend /app/web/build ./web/build
RUN APP_ENV=test SECRET_KEY=build-only-configuration-not-a-runtime-secret ALLOWED_HOSTS=localhost DATABASE_URL=postgresql://localhost/build .venv/bin/python manage.py collectstatic --noinput     && groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
USER app
EXPOSE 8000
CMD [".venv/bin/gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
