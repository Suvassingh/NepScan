FROM python:3.11-slim

WORKDIR /app

COPY requirements-celery.txt .
RUN pip install --no-cache-dir -r requirements-celery.txt

COPY . .

CMD [\"celery\", \"-A\", \"config\", \"worker\", \"--loglevel=info\", \"--pool=solo\"]
