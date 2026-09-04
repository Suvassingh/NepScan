import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

app = Celery('scanline_backend')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    worker_pool='solo',
    worker_state_db=None,
)

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
