from celery import Celery
import os

# Connect to Redis.
# If running in Docker, hostname might be 'redis', but locally it's 'localhost'.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "jarvis_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Periodic Tasks
celery_app.conf.beat_schedule = {
    # 'scan-all-directories-every-hour': {
    #     'task': 'backend.app.tasks.scan_all_directories',
    #     'schedule': 3600.0, # 1 hour
    # },
}

