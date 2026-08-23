from .base import *
from .security import *    

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '10.0.2.2']

 
KMS_BACKEND = 'local'
if not LOCAL_DEV_MASTER_KEY:
 
    import base64, os
    LOCAL_DEV_MASTER_KEY = base64.b64encode(os.urandom(32)).decode()
    print(f"Generated LOCAL_DEV_MASTER_KEY: {LOCAL_DEV_MASTER_KEY}")
 
SECURE_SSL_REDIRECT = False

 
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdnjs.cloudflare.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com")
# Enable debug toolbar if installed
if 'debug_toolbar' in INSTALLED_APPS:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
 

import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': os.environ.get('SUPABASE_DB_PASSWORD'),
        'HOST': os.environ.get('SUPABASE_DB_HOST'),
        'PORT': '5432',
        'OPTIONS': {'sslmode': 'require'},
    }
}