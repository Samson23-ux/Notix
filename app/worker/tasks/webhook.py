import httpx
from uuid import uuid4, UUID
from datetime import datetime, timezone
from resend.exceptions import ResendError
from celery.exceptions import Reject


from app.worker import celery_app
from app.core.security import Security
from app.core.config import get_settings
from app.worker import BaseTaskWithFailure
from app.core.exceptions import MaxRetriesError
from app.api.models.notification import Notification
from app.worker import (
    get_redis_repo,
    get_request_service,
    get_notification_service,
)

SECURITY = Security()
SETTINGS = get_settings()


@celery_app.task(base=BaseTaskWithFailure, bind=True)
def deliver_webhook_task(
    self,
    notification_id: UUID,
    idempotency_key: str,
    secret: str,
    webhook_url: str,
    payload: dict,
):
    try:
        redis_repo = get_redis_repo()
        request = get_request_service()
        notification_service = get_notification_service()

        key: str = f"idempotency:{idempotency_key}"
        already_processed: str | None = redis_repo.get_processed_email(key)

        notification: Notification = notification_service._get_notification(
            notification_id
        )

        if not already_processed:
            headers: dict = {
                "x_notix_signature": SECURITY.sign_payload(secret, payload),
                "x_notix_delivery_id": uuid4(),
                "x_notix_idempotency_key": idempotency_key,
            }
            request.sync_post(url=webhook_url, headers=headers)

            redis_repo.mark_email_processed(key, "1", SETTINGS.IDEMPOTENCY_KEY_TTL)

            notification.status = "delivered"
            notification.delivered_at = datetime.now(timezone.utc)
            notification_service.update_notification(notification)
    except (
        ResendError,
        httpx.ConnectError,
        httpx.ConnectTimeout,
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
                exc, self.request.kwargs, "notification", self.request.retries
            )

            notification.dead_lettered_at = datetime.now(timezone.utc)
            raise Reject(exc, requeue=False)
    except httpx.HTTPStatusError as exc:
        """Retry for errors with 500 status code and send to dlq for client errors"""
        if exc.response.status_code >= 500:
            try:
                raise self.retry(
                    exc=MaxRetriesError(str(exc)), countdown=self._backoff_countdown()
                )
            except MaxRetriesError as exc:
                self._handle_failure(
                    exc, self.request.kwargs, "notification", self.request.retries
                )

                notification.dead_lettered_at = datetime.now(timezone.utc)
                raise Reject(exc, requeue=False)
    except Exception as exc:
        """Update state and reject manaully to send to dlq for non-transient errors"""
        self._handle_failure(
            exc, self.request.kwargs, "notification", self.request.retries
        )

        notification.dead_lettered_at = datetime.now(timezone.utc)
        raise Reject(exc, requeue=False)
    finally:
        request.close()
        redis_repo._sync_redis.close()
        notification_service._notis_repo.close()
