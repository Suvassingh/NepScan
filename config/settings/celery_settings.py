import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = 'django-insecure-for-celery-only'
DEBUG = False
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_celery_results',
    'apps.jobs',
    'apps.conversion',
    'apps.pdf_tools',
    'apps.billing',
    'apps.ocr',
]

MIDDLEWARE = []
ROOT_URLCONF = None

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {'sslmode': 'require'},
    }
}

# ? Read from environment variable
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# ? Convert to rediss:// if needed
if REDIS_URL.startswith('redis://'):
    REDIS_URL = REDIS_URL.replace('redis://', 'rediss://')

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = 'django-db'
CELERY_WORKER_POOL = 'solo'
CELERY_WORKER_STATE_DB = None
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

TIME_ZONE = 'UTC'
USE_TZ = True

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
