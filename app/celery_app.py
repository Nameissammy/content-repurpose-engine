from celery import Celery
from app.config import settings

celery_app = Celery(
    "content_repurpose",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.ingestion",
        "app.workers.content_generation",
        "app.workers.publishing",
        "app.workers.notifications",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=settings.MAX_CONCURRENT_JOBS,
)

# Task routes
celery_app.conf.task_routes = {
    "app.workers.ingestion.*": {"queue": "ingestion"},
    "app.workers.content_generation.*": {"queue": "generation"},
    "app.workers.publishing.*": {"queue": "publishing"},
    "app.workers.notifications.*": {"queue": "notifications"},
}
