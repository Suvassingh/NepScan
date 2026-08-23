from .base import *
from .security import *

DEBUG = True
ALLOWED_HOSTS = ['*']

 
DATABASES['default']['NAME'] = 'test_scanline'
DATABASES['default']['USER'] = 'test_user'
DATABASES['default']['PASSWORD'] = 'test_pass'

 
KMS_BACKEND = 'local'
LOCAL_DEV_MASTER_KEY = 'c2VjcmV0LWtleS0zMi1ieXRlcy1mb3ItdGVzdGluZw=='  # base64 of 32 bytes
 
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}