FROM python:3.11-slim

WORKDIR /app

COPY requirements-celery.txt .
RUN pip install --no-cache-dir -r requirements-celery.txt

COPY . .

CMD [\"sh\", \"-c\", \"DJANGO_SETTINGS_MODULE=config.settings.celery_settings celery -A config worker --loglevel=info --pool=solo\"]
