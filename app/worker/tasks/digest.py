import psycopg2
from celery import states
from sqlalchemy import Sequence
from datetime import datetime, timezone
from resend.exceptions import ResendError
from celery.exceptions import MaxRetriesExceededError, Reject


from app.core.config import get_settings
from app.worker.celery_app import celery_app
from app.api.models.notification import Notification
from app.worker.tasks.base import BaseTaskWithFailure
from app.worker.tasks.services import (
    get_redis_repo,
    get_email_service,
    get_notification_service,
)

SETTINGS = get_settings()


@celery_app.task(base=BaseTaskWithFailure, bind=True)
def collect_and_send_digests(self):
    redis_repo = get_redis_repo()
    email_service = get_email_service()
    notification_service = get_notification_service()

    try:
        notification_digest: Sequence[Notification] = (
            notification_service.get_digest_notifications()
        )

        for digest in notification_digest:
            email_service.api_key = SETTINGS.RESEND_API_KEY
            email_service.send(
                SETTINGS.API_EMAIL,
                digest.recipient,
                digest.subject,
                digest.body
            )

            digest.status = "delivered"
            digest.delivered_at = datetime.now(timezone.utc)

            notification_service.update_notification(digest)
    except (
        ResendError,
        psycopg2.OperationalError,
        psycopg2.InterfaceError,
        psycopg2.extensions.TransactionRollbackError,
    ) as exc:
        """retry for transient errors"""
        if isinstance(exc, ResendError):
            if hasattr(exc, "code") and exc.code >= 500:
                raise self.retry(exc=exc)
        raise self.retry(exc=exc)
    except (Exception, MaxRetriesExceededError) as exc:
        """Update state and reject manaully to send to dlq for non-transient errors"""
        notification_id = digest.id
        self.update_state(
            state=states.FAILURE,
            meta={
                "record_id": notification_id,
                "type": "notification",
                "details": str(exc),
                "retries": self.request.retries,
            },
        )

        digest.dead_lettered_at = datetime.now(timezone.utc)
        raise Reject(exc, requeue=False)
    finally:
        redis_repo._sync_redis.close()
        email_service._email_repo.close()
        notification_service._notis_repo.close()
