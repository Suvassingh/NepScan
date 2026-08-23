from .base import *
from .security import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

 
KMS_BACKEND = 'aws'
KMS_KEY_ARN = os.environ['KMS_KEY_ARN']
KMS_REGION = os.environ.get('KMS_REGION', 'ap-south-1')
SHARE_TOKEN_PEPPER = os.environ['SHARE_TOKEN_PEPPER']

 
CLAMAV_SOCKET = os.environ.get('CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')

 
DATABASES['default']['OPTIONS']['sslmode'] = 'require'
 
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
 