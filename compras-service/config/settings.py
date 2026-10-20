from pathlib import Path

from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config(
    "SECRET_KEY"
)


DEBUG = config(
    "DEBUG",
    default=False,
    cast=bool
)


ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost"
).split(",")


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "compras",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]


ROOT_URLCONF = "config.urls"


WSGI_APPLICATION = "config.wsgi.application"


CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000"
).split(",")


CORS_ALLOW_CREDENTIALS = True


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",

        "NAME": config(
            "DB_NAME"
        ),

        "USER": config(
            "DB_USER"
        ),

        "PASSWORD": config(
            "DB_PASSWORD"
        ),

        "HOST": config(
            "DB_HOST",
            default="localhost"
        ),

        "PORT": config(
            "DB_PORT",
            default="5432"
        ),

        "OPTIONS": {
            "options": (
                f"-c search_path="
                f"{config('DB_SCHEMA', default='compras_schema')}"
            ),
        },
    }
}


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "common.jwt_authentication.CookieJWTAuthentication"
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"
    ],
}


JWT_PUBLIC_KEY_PATH = (
    BASE_DIR / config(
        "JWT_PUBLIC_KEY_PATH"
    )
)


JWT_ISSUER = config(
    "JWT_ISSUER",
    default="auth-service"
)


LANGUAGE_CODE = "es-co"


TIME_ZONE = "America/Bogota"


USE_I18N = True

USE_TZ = True


DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


STATIC_URL = "static/"