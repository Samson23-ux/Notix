import psycopg2
from sqlalchemy import Sequence
from datetime import datetime, timezone
from resend.exceptions import ResendError
from celery.exceptions import Reject


from app.worker import celery_app
from app.core.config import get_settings
from app.worker import BaseTaskWithFailure
from app.core.exceptions import MaxRetriesError
from app.api.models.notification import Notification

SETTINGS = get_settings()


@celery_app.task(base=BaseTaskWithFailure, bind=True)
def collect_and_send_digests(self):
    from app.worker import get_redis_repo, get_email_service, get_notification_service

    redis_repo = get_redis_repo()
    email_service = get_email_service()
    notification_service = get_notification_service()

    try:
        notification_digest: Sequence[Notification] = (
            notification_service.get_digest_notifications()
        )

        for digest in notification_digest:
            current_status: str = digest.status
            email_service.api_key = SETTINGS.RESEND_API_KEY
            email_service.send(
                SETTINGS.API_EMAIL, digest.recipient, digest.subject, digest.body
            )

            digest.status = "delivered"
            digest.delivered_at = datetime.now(timezone.utc)

            """Update if message is decided to be re-queued manually from dlq"""
            if current_status == "failed":
                digest.failed_at = None
                digest.retry_count = None
                digest.faliure_reason = None
                digest.dead_lettered_at = None

            notification_service.update_notification(digest)
    except (
        ResendError,
        psycopg2.OperationalError,
        psycopg2.InterfaceError,
        psycopg2.extensions.TransactionRollbackError,
    ) as exc:
        """retry for transient errors"""
        try:
            if isinstance(exc, ResendError):
                if hasattr(exc, "code") and exc.code >= 500:
                    raise self.retry(
                        exc=MaxRetriesError(str(exc)),
                        countdown=self._backoff_countdown(),
                    )
            raise self.retry(
                exc=MaxRetriesError(str(exc)), countdown=self._backoff_countdown()
            )
        except MaxRetriesError as exc:
            self._handle_failure(
                exc, {"notification_id": digest.id}, "notification", self.request.retries
            )

            digest.dead_lettered_at = datetime.now(timezone.utc)
            notification_service.update_notification(digest)
            raise Reject(exc, requeue=False)
    except Exception as exc:
        """Update state and reject manaully to send to dlq for non-transient errors"""
        self._handle_failure(
            exc, self.request.kwargs, "notification", self.request.retries
        )

        digest.dead_lettered_at = datetime.now(timezone.utc)
        notification_service.update_notification(digest)
        raise Reject(exc, requeue=False)
    finally:
        redis_repo._sync_redis.close()
        email_service._email_repo.close()
        notification_service._notis_repo.close()
