from celery import Celery


from app.core.config import get_settings

celery_app = Celery(
    main="celery_app",
    broker=get_settings().BROKER_URL,
    backend=get_settings().REDIS_URL,
)


celery_app.config_from_object("app.worker.celeryconfig")
celery_app.autodiscover_tasks(
    [
        "app.worker.tasks.dlq",
        "app.worker.tasks.email",
        "app.worker.tasks.digest",
        "app.worker.tasks.webhook",
    ]
)
