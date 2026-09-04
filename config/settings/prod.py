import os
from .base import *
from .security import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

REDIS_URL = os.environ.get('REDIS_URL', '')

if REDIS_URL.startswith('redis://'):
    REDIS_URL = REDIS_URL.replace('redis://', 'rediss://')

if not REDIS_URL:
    REST_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
    if REST_URL:
        REDIS_URL = REST_URL.replace('https://', 'rediss://') + ':6379'

if not REDIS_URL:
    REDIS_URL = 'redis://localhost:6379/0'

if REDIS_URL.startswith('rediss://') and 'ssl_cert_reqs' not in REDIS_URL:
    REDIS_URL = REDIS_URL + '?ssl_cert_reqs=CERT_NONE'

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

cors_allowed = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if cors_allowed == '*':
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []
else:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_allowed.split(',') if origin.strip()]
    CORS_ALLOW_ALL_ORIGINS = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {'sslmode': 'require'},
    }
}

KMS_BACKEND = os.environ.get('KMS_BACKEND', 'local')
LOCAL_DEV_MASTER_KEY = os.environ.get('LOCAL_DEV_MASTER_KEY')
SHARE_TOKEN_PEPPER = os.environ.get('SHARE_TOKEN_PEPPER', 'your-strong-secret')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}