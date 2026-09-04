import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-me')
DEBUG = False
ALLOWED_HOSTS = []
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

INSTALLED_APPS = [
    'unfold',
    'apps.admin_panel',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'csp',
    'django_celery_results',
    'apps.authentication',
    'apps.audit',
    'apps.ocr',
    'apps.pdf_tools',
    'apps.ai_assist',
    'apps.expense',
    'apps.conversion',
    'apps.id_card',
    'apps.jobs',
    'apps.billing',
    'apps.voice_notes',
    'apps.supabase_models',
    'apps.workspaces',
    'apps.image_processing',
    'apps.annotations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.DocumentAccessAuditMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'apps' / 'admin_panel' / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'scanline'),
        'USER': os.environ.get('DB_USER', 'scanline'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.environ.get('DB_SSLMODE', 'require'),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REDIS_URL = os.environ.get('REDIS_URL', '')

if REDIS_URL.startswith('redis://'):
    REDIS_URL = REDIS_URL.replace('redis://', 'rediss://')

if not REDIS_URL:
    REDIS_URL = os.environ.get('UPSTASH_REDIS_REST_URL', '')
    if REDIS_URL:
        REDIS_URL = REDIS_URL.replace('https://', 'rediss://') + ':6379'

if not REDIS_URL:
    REDIS_URL = 'redis://localhost:6379/0'

if REDIS_URL.startswith('rediss://') and 'ssl_cert_reqs' not in REDIS_URL:
    REDIS_URL = REDIS_URL + '?ssl_cert_reqs=CERT_NONE'

CELERY_BROKER_URL = REDIS_URL
CELERY_WORKER_STATE_DB = None
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_WORKER_POOL = 'solo'

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = os.environ['SUPABASE_SERVICE_ROLE_KEY']
SUPABASE_JWKS_URL = os.environ['SUPABASE_JWKS_URL']
SUPABASE_JWT_AUDIENCE = os.environ['SUPABASE_JWT_AUDIENCE']
SUPABASE_JWT_ISSUER = os.environ['SUPABASE_JWT_ISSUER']

KMS_BACKEND = os.environ.get('KMS_BACKEND', 'local')
KMS_KEY_ARN = os.environ.get('KMS_KEY_ARN', '')
KMS_REGION = os.environ.get('KMS_REGION', 'ap-south-1')
LOCAL_DEV_MASTER_KEY = os.environ.get('LOCAL_DEV_MASTER_KEY', '')
SHARE_TOKEN_PEPPER = os.environ['SHARE_TOKEN_PEPPER']

CLAMAV_SOCKET = os.environ.get('CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')
ALLOWED_UPLOAD_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'application/pdf'}
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.authentication.backends.SupabaseJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'ocr': '20/hour',
        'pdf_protect': '30/hour',
        'auth': '10/minute',
        'expense_export': '10/hour',
        'default': '200/hour',
    },
    'EXCEPTION_HANDLER': 'common.exceptions.sanitized_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}