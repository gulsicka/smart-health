from celery import Celery
from config import settings

app = Celery(
    "notification-service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["tasks"],  # tells Celery where to find the tasks
)
