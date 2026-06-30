from celery import Celery


from app.core.config import get_settings

celery_app = Celery(
    main="celery_app",
    broker=get_settings().API_BROKER,
    backend=get_settings().REDIS_URL,
)


celery_app.config_from_object("app.task.celeryconfig")
celery_app.autodiscover_tasks(["app.worker.tasks"])
