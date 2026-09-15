from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("pulsewatch", broker=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Discover tasks defined in domain modules
celery_app.autodiscover_tasks(["app.incident"])
