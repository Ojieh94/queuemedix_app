from celery import Celery
from core.celery import app as celery_app

# Optional: autodiscover tasks
celery_app.autodiscover_tasks(["core.celery"])
