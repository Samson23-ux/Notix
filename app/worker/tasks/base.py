from uuid import UUID
from celery.result import AsyncResult
from datetime import datetime, timezone


from app.worker import celery_app
from app.api.models.email import Email
from app.api.models.notification import Notification

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

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from app.worker import get_notification_service, get_email_service

        try:
            email_service = get_email_service()
            notification_service = get_notification_service()

            result = AsyncResult(task_id)
            result_info: dict = result.info

            type: str = result_info.get("type")

            if type == "verification":
                email_id: UUID = UUID(result_info.get("record_id"))
                email: Email = email_service.get_proccessed_email(email_id)

                email.status = "failed"
                email.failed_at = datetime.now(timezone.utc)
                email_service.update_processed_email(email)
            else:
                notification_id: UUID = UUID(result_info.get("record_id"))
                notification: Notification = notification_service._get_notification(
                    notification_id
                )

                notification.status = "failed"
                notification.retry_count("retries")
                notification.failed_at = datetime.now(timezone.utc)
                notification.faliure_reason(result_info.get("details"))

                notification_service.update_notification(notification)
        finally:
            email_service._email_repo.close()
            notification_service._notis_repo.close()
