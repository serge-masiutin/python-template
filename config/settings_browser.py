"""Isolated persistent SQLite database for browser tests only."""

from .settings_test import *  # noqa: F403
from .settings_test import BASE_DIR

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "tmp/browser.sqlite3"}
}

MIDDLEWARE = [MIDDLEWARE[0], "whitenoise.middleware.WhiteNoiseMiddleware", *MIDDLEWARE[1:]]  # noqa: F405
