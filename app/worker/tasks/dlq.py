from sentry_sdk import logger as sentry_logger


from app.worker.celery_app import celery_app
from app.worker.tasks.services import get_event_channel


@celery_app.task
def monitor_dlq():
    try:
        channel = get_event_channel()

        depth = channel.sync_queue_depth("notix.dlq")
        sentry_logger.info("Current queue depth: {depth}", depth=depth)

        if depth > 100:
            sentry_logger.fatal(
                "CRITICAL: Maximum DLQ depth reached. Current depth: {depth}",
                depth=depth,
            )
    finally:
        channel.close()
