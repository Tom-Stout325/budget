"""
Django settings for project project.

Target: local/dev only (SQLite + CSV uploads + WeasyPrint PDFs)
Docs: https://docs.djangoproject.com/en/5.2/topics/settings/
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------
# SECURITY (dev-friendly, still "secure by default")
# --------------------------------------------------------------------
# ✅ New random key (replace with env var for anything beyond local dev)
# Recommended: export DJANGO_SECRET_KEY="..." and use that instead.
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-4o#s(8e7z%t4t8u1a$0c^v5b3m7kq!d2x9y6p1n0r3w8h5j2l7",
)

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# --------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd-party (from your trimmed requirements list)
    "crispy_forms",
    "crispy_bootstrap5",
    "formtools",

    # Project apps
    "accounts",
    "budget",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --------------------------------------------------------------------
# Middleware
# --------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

# --------------------------------------------------------------------
# Templates
# --------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # ✅ custom
                "project.context_processors.current_page",
            ],
        },
    },
]


WSGI_APPLICATION = "project.wsgi.application"

# --------------------------------------------------------------------
# Database (temporary SQLite)
# --------------------------------------------------------------------
# Uses OS temp directory. Delete the file any time to reset your data.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.getenv("SQLITE_TMP_PATH", "/tmp/budget_dev.sqlite3")),
    }
}

# --------------------------------------------------------------------
# Password validation
# --------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------
# Internationalization
# --------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------
# Static & Media (CSV uploads will typically use MEDIA)
# --------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # put your dev assets here
STATIC_ROOT = BASE_DIR / "staticfiles"    # collectstatic output (prod-like)

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"           # uploaded CSVs go here if you store them

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
