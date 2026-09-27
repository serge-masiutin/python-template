"""Environment and framework configuration; invalid required settings fail at startup."""

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder

BASE_DIR = Path(__file__).resolve().parent.parent
APP_ENV = os.environ.get("APP_ENV", "production")
if APP_ENV not in {"development", "production", "test"}:
    raise ImproperlyConfigured("APP_ENV must be development, production or test")
DEBUG = APP_ENV == "development"
SECRET_KEY = os.environ["SECRET_KEY"]
if len(SECRET_KEY) < 32:
    raise ImproperlyConfigured("SECRET_KEY must have at least 32 characters")
ALLOWED_HOSTS = [host.strip() for host in os.environ["ALLOWED_HOSTS"].split(",")]
if not all(ALLOWED_HOSTS) or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must list explicit hosts")
database = urlparse(os.environ["DATABASE_URL"])
if (
    database.scheme not in {"postgres", "postgresql"}
    or not database.hostname
    or not database.path.strip("/")
):
    raise ImproperlyConfigured("DATABASE_URL must identify a PostgreSQL host and database")
if database.query or database.fragment:
    raise ImproperlyConfigured(
        "Use explicit database settings instead of DATABASE_URL query/fragment"
    )
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(database.path[1:]),
        "USER": unquote(database.username or ""),
        "PASSWORD": unquote(database.password or ""),
        "HOST": database.hostname,
        "PORT": database.port or 5432,
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_vite",
    "inertia",
    "accounts",
    "notes",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.shared_props",
    "inertia.middleware.InertiaMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login/"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "web/build"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
DJANGO_VITE = {
    "default": {"dev_mode": DEBUG, "manifest_path": BASE_DIR / "web/build/manifest.json"}
}
INERTIA_LAYOUT = "base.html"
# Fail on model/queryset props instead of using the adapter's implicit model_to_dict encoder.
INERTIA_JSON_ENCODER = DjangoJSONEncoder
INERTIA_VERSION = os.environ["ASSET_VERSION"] if APP_ENV == "production" else "development"
INERTIA_ENCRYPT_HISTORY = APP_ENV == "production"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG and APP_ENV != "test"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_SSL_REDIRECT = SESSION_COOKIE_SECURE
SECURE_HSTS_SECONDS = 31536000 if SESSION_COOKIE_SECURE else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SESSION_COOKIE_SECURE
SECURE_HSTS_PRELOAD = SESSION_COOKIE_SECURE
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
