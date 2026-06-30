"""
Django settings for config project (Japan HF Ownership Tracker).

Ported from the original Streamlit app (app.py).
Key production-related values are read from environment variables so the same
codebase runs locally and on Azure App Service without code changes.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Security / environment
# --------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-key-change-me-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",")

CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]


# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tracker",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves static files in production (pip install whitenoise).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# WhiteNoise is optional in pure-dev mode. If it is not installed, drop it so
# `runserver` still works out of the box.
try:
    import whitenoise  # noqa: F401
except ModuleNotFoundError:
    MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --------------------------------------------------------------------------
# Database
# Default: SQLite (mirrors the original data/cache.db cache).
# Set DATABASE_URL (postgres://...) on Azure for a managed DB.
# --------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    try:
        import dj_database_url

        DATABASES["default"] = dj_database_url.parse(
            _database_url, conn_max_age=600
        )
    except ModuleNotFoundError:
        # dj-database-url not installed; keep SQLite fallback.
        pass


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------------------------------------------------------
# Internationalization
# TIME_ZONE / USE_TZ are env-overridable. The app stores quarter-end *dates*,
# so timezone handling is not critical, but Asia/Tokyo is the sensible default.
# --------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Tokyo")
USE_I18N = True
USE_TZ = os.environ.get("DJANGO_USE_TZ", "True") == "True"


# --------------------------------------------------------------------------
# Static files
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
