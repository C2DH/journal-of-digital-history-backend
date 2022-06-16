"""
Django settings for jdh project.

Generated by 'django-admin startproject' using Django 3.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os
from .base import get_env_variable

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_variable('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_env_variable('DEBUG', 'True')

DJANGO_LOG_LEVEL = get_env_variable('DJANGO_LOG_LEVEL', 'DEBUG')

ALLOWED_HOSTS = get_env_variable('ALLOWED_HOSTS', 'localhost').split(',')

DRF_RECAPTCHA_SECRET_KEY = get_env_variable('DRF_RECAPTCHA_SECRET_KEY')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard.apps.DashboardConfig',
    'rest_framework',
    'jdhapi.apps.JdhapiConfig',
    'jdhseo.apps.JdhseoConfig',
    'jdhtasks.apps.JdhtasksConfig',
    # to use Bootsrap
    'crispy_forms',
    'drf_recaptcha',
    'django_filters',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10
}

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jdh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'jdh.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': get_env_variable('DATABASE_ENGINE'),  # 'django.db.backends.postgresql_psycopg2',
        'NAME': get_env_variable('DATABASE_NAME'),
        'USER': get_env_variable('DATABASE_USER'),
        'PASSWORD': get_env_variable('DATABASE_PASSWORD'),
        'HOST': get_env_variable('DATABASE_HOST', 'localhost'),
        'PORT': get_env_variable('DATABASE_PORT', '54320'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True


JDH_SCHEMA_ROOT = get_env_variable(
    'JDH_SCHEMA_ROOT',
    os.path.join(BASE_DIR, 'schema')
)
# Current version
JDH_GIT_BRANCH = get_env_variable('JDH_GIT_BRANCH', 'nd')
JDH_GIT_REVISION = get_env_variable('JDH_GIT_REVISION', 'nd')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATIC_URL = get_env_variable('STATIC_URL', '/static/')
STATIC_ROOT = get_env_variable('STATIC_ROOT', '/static')
STATICFILES_DIRS = [
    # ...
    ('schema', JDH_SCHEMA_ROOT),
]

MEDIA_URL = get_env_variable('MEDIA_URL', '/media/')
MEDIA_ROOT = get_env_variable('MEDIA_ROOT', '/media')

# ACCOUNT_EMAIL_VERIFICATION = 'none'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Host for sending e-mail.
EMAIL_HOST = get_env_variable('EMAIL_HOST', 'smtp.')

# Port for sending e-mail.
EMAIL_PORT = get_env_variable('EMAIL_PORT', 0)

# Number of words to take into account for the fingerprint
NUM_CHARS_FINGERPRINT = get_env_variable('NUM_CHARS_FINGERPRINT', 5)

# Token id to connect to the ORCID API for the user JDH JDH
JDH_ORCID_API_TOKEN = get_env_variable('JDH_ORCID_API_TOKEN', 0)

# in settings, no request to Google, no warnings,
DRF_RECAPTCHA_TESTING = get_env_variable('DRF_RECAPTCHA_TESTING', 'False') == 'True'


# ADD logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'jdhseo.views': {
            'handlers': ['console'],
            'level': get_env_variable('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
    },
    'formatters': {
        'verbose': {
            # 'format': '%(levelname)s %(asctime)s %(module)s %(process)d
            # %(thread)d %(message)s'
            'format': '{levelname} {asctime} - {name:s} L{lineno:d}: {message}',
            'style': '{',
        },
    },
    'simple': {
        'format': '{levelname} {message}',
        'style': '{',
    },
}

# Celery
REDIS_HOST = get_env_variable('REDIS_HOST', 'localhost')
REDIS_PORT = get_env_variable('REDIS_PORT', '6379')
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/4'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/5'
CELERYD_PREFETCH_MULTIPLIER = 2
CELERYD_CONCURRENCY = 2

# jdhseo
JDHSEO_PROXY_HOST = get_env_variable(
    'JDHSEO_PROXY_HOST', 'https://journalofdigitalhistory.org/')
JDHSEO_PROXY_PATH_GITHUB = get_env_variable(
    'JDHSEO_PROXY_PATH_GITHUB', '/proxy-githubusercontent')
