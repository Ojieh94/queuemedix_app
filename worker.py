from src.app.core.celery import app as celery_app

# Optional: autodiscover tasks
celery_app.autodiscover_tasks(["src.app.core.celery"])
