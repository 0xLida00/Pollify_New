"""
Django settings for pollify_project project.

Generated by 'django-admin startproject' using Django 4.2.16.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from django.contrib.messages import constants as messages
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-e!43f16-5n6^r^03$e+sqju-kj)!e$$d*l+h&_+s^(1jaq=a9w'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'pollify-polls-projects.onrender.com']

# Login and Logout settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Application definition

INSTALLED_APPS = [
    'daphne', # Django Channels ASGI server
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps
    'channels', # WebSockets support
    'users',
    'polls',
    'comments',
    'notifications',
    'messaging',
    'admin_panel',
    'frontend',
    'crispy_forms',
    'crispy_bootstrap4',

    # Third-party apps
    'rest_framework',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap", "bootstrap4")
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Set ASGI application
ASGI_APPLICATION = "pollify_project.asgi.application"

# Configure Redis for WebSocket communication
# Use Upstash Redis URL from environment variable, fallback to local Redis for development
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")

# Configure Redis for WebSocket communication
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],  # Use Upstash Redis dynamically
        },
    },
}

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CACHE SETTINGS (Prevents Follow State Reset)
CACHE_MIDDLEWARE_SECONDS = 0  # Forces fresh database reads
CACHE_MIDDLEWARE_KEY_PREFIX = "pollify"

ROOT_URLCONF = 'pollify_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'messaging.context_processors.unread_messages_count',
                'notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'pollify_project.pollify_project.wsgi.application'


# Custom user model
AUTH_USER_MODEL = 'users.User'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600)
    }

# Force PostgreSQL in production (Render)
if os.getenv("RENDER") or os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config(conn_max_age=600, ssl_require=True)

SESSION_ENGINE = "django.contrib.sessions.backends.db"  # Store session data in DB
SESSION_COOKIE_SECURE = not DEBUG  # Secure cookies in production
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep session even after browser closes

# SECURITY & CSRF SETTINGS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Ensure correct HTTPS detection
SECURE_SSL_REDIRECT = not DEBUG  # Redirect all HTTP traffic to HTTPS in production

# CSRF and CORS trusted origins (prevents CSRF token issues)
CSRF_TRUSTED_ORIGINS = ["https://pollify-polls-projects.onrender.com"]
CORS_ALLOWED_ORIGINS = ["https://pollify-polls-projects.onrender.com"]

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Handle media storage in production
if not DEBUG:  # Deployment mode (Render)
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION')  # Optional: set region
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

if os.getenv("DEBUG", "True") == "True":
    os.makedirs(MEDIA_ROOT, exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'