from app.worker.celery_app import celery_app


class BaseTaskWithFailure(celery_app.Task):
    # maximum retry value
    max_retries = 5

    """
    retry jitter set to True to ensure randomness in retry_backoff value
    this prevents overwhelming when multiple tasks fails simultaneously,
    retrying each task at different time
    """
    retry_jitter = True

    """
    increment retry delay value exponentially
    """
    retry_backoff = 2

    """
    maximum retry backoff - one minute
    """
    retry_backoff_max = 600
