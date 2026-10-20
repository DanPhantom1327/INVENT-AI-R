"""
Ruta: auth-service/config/settings.py
Paso 1: configuracion base. El bloque de JWT/RS256 se agrega en el Paso 2.
"""
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "usuarios",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000").split(",")
CORS_ALLOW_CREDENTIALS = True

# --- Base de datos: PostgreSQL, esquema auth_schema (Fase 3) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "OPTIONS": {"options": f"-c search_path={config('DB_SCHEMA', default='auth_schema')}"},
    }
}

AUTH_USER_MODEL = "usuarios.Usuario"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["common.jwt_authentication.CookieJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}


LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"

# --- JWT / JWS (RS256) ---
JWT_PRIVATE_KEY_PATH = BASE_DIR / config("JWT_PRIVATE_KEY_PATH")
JWT_PUBLIC_KEY_PATH = BASE_DIR / config("JWT_PUBLIC_KEY_PATH")
JWT_ACCESS_TOKEN_MINUTES = config("JWT_ACCESS_TOKEN_MINUTES", default=15, cast=int)
JWT_REFRESH_TOKEN_DAYS = config("JWT_REFRESH_TOKEN_DAYS", default=7, cast=int)
JWT_ISSUER = config("JWT_ISSUER", default="auth-service")
JWT_ALGORITHM = "RS256"

# --- Cookies httpOnly ---
COOKIE_SECURE = config("COOKIE_SECURE", default=True, cast=bool)
COOKIE_SAMESITE = config("COOKIE_SAMESITE", default="Lax")
