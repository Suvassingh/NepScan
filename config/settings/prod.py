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

# Celery Broker
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
cors_allowed = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if cors_allowed == '*':
    # Invalid wildcard – ignore it and allow all origins
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []
else:
    # Parse comma‑separated list of valid origins
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_allowed.split(',') if origin.strip()]
    CORS_ALLOW_ALL_ORIGINS = False

 
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database – Supabase PostgreSQL
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

# Share token pepper
SHARE_TOKEN_PEPPER = os.environ.get('SHARE_TOKEN_PEPPER', 'your-strong-secret')

# OpenAI (if used)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Static files (Whitenoise)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging – send to console (Render captures logs)
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