from celery import Celery
from kombu import Queue

# celery_app = Celery(
#     "resume_tasks",
#     broker="redis://localhost:6379/0",
#     backend="redis://localhost:6379/1"
# )


celery_app = Celery(
    "resume_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.features.resume.workers.resume_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,

    broker_transport_options={
        "visibility_timeout": 3600
    },

    result_expires=3600,
    timezone="UTC",
    enable_utc=True,
    broker_pool_limit=10,

    task_queues=(
        Queue("high_priority"),
        Queue("default"),
        Queue("low_priority"),
    ),

    task_routes={
        "app.features.resume.workers.resume_tasks.process_resume_task": {
            "queue": "high_priority"
        }
    }
)