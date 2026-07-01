import sentry_sdk
from uuid import UUID
from sqlalchemy import Sequence
import sentry_sdk.logger as sentry_logger


from app.api.models.user import User
from app.core.config import get_settings
from app.api.services.channel import EventChannel
from app.api.models.webhook import WebhookEndpoint
from app.api.services.webhook import WebhookService
from app.api.models.notification import Notification
from app.worker.tasks.webhook import deliver_webhook_task
from app.api.repo.notification import NotificationRepository
from app.worker.tasks.email import send_email_task, send_critical_email_task
from app.api.schemas.notification import (
    EmailNotification,
    WebhookNotification,
    NotificationResponse,
)
from app.core.exceptions import (
    ServerError,
    UrlNotFoundError,
    ServiceUnavailable,
    NotificationExistsError,
    NotificationNotFoundError,
)


class NotificationService:
    def __init__(self, notis_repo: NotificationRepository):
        self._notis_repo = notis_repo

    SETTINGS = get_settings()

    QUEUE_MAP = {
        "high": "notix.high",
        "low": "notix.standard",
        "critical": "notix.high",
        "medium": "notix.standard",
    }

    PRIORITY_MAP = {
        "high": 8,
        "low": 2,
        "critical": 10,
        "medium": 5,
    }

    def _get_user_email(self, user: User) -> str:
        if user.type == "email":
            user_email: str = user.email
        elif user.type == "github":
            user_email: str = user.github_email
        else:
            user_email: str = user.google_email

        return user_email

    async def create_email_notification(
        self, channel: EventChannel, curr_user: User, payload: EmailNotification
    ) -> NotificationResponse:
        type: str = payload.type.lower()
        priority: str = payload.priority.lower()
        idempotency_key: str = payload.idempotency_key

        user_email: str = self._get_user_email(curr_user)
        queue: str = self.QUEUE_MAP.get(priority, "notix.standard")

        notification_db: Notification | None = await self._notis_repo.get_record(
            idempotency_key=idempotency_key
        )

        if notification_db:
            sentry_logger.error(
                "Notification exists with the idempotency_key: {idempotency_key}",
                idempotency_key=idempotency_key,
            )
            raise NotificationExistsError(key=idempotency_key)

        current_depth: int = await channel.queue_depth(queue)

        if current_depth > self.SETTINGS.MAXIMUM_QUEUE_DEPTH:
            sentry_logger.error("Maximum depth reached for queue {queue}", queue=queue)
            raise ServiceUnavailable()

        try:
            await self._notis_repo.add(entity=payload)
            await self._notis_repo.commit()
            sentry_logger.info(
                "Email Notification created successfully for user {email}",
                email=user_email,
            )

            notification_db: Notification | None = await self._notis_repo.get_record(
                idempotency_key=idempotency_key
            )

            ### send to worker
            if type == "email":
                if priority == "critical" or priority == "high":
                    send_critical_email_task.appy_async(
                        priority=self.PRIORITY_MAP.get(priority),
                        kwargs={
                            "notification_id": notification_db.id,
                            "idempotency_key": idempotency_key,
                            "recipient_email": user_email,
                            "subject": payload.subject,
                            "body": payload.body,
                        },
                    )
                else:
                    send_email_task.appy_async(
                        priority=self.PRIORITY_MAP.get(priority),
                        kwargs={
                            "notification_id": notification_db.id,
                            "idempotency_key": idempotency_key,
                            "recipient_email": user_email,
                            "subject": payload.subject,
                            "body": payload.body,
                        },
                    )

            return NotificationResponse.model_validate(notification_db)
        except Exception as e:
            await self._notis_repo.rollback()
            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while creating email notification for user {email}",
                email=user_email,
            )
            raise ServerError() from e

    async def create_webhook_notification(
        self,
        curr_user: User,
        channel: EventChannel,
        payload: WebhookNotification,
        webhook_service: WebhookService,
    ) -> NotificationResponse:
        url: str = payload.webhook_url
        idempotency_key: str = payload.idempotency_key

        user_email: str = self._get_user_email(curr_user)
        queue: str = self.QUEUE_MAP.get(payload.priority, "notix.standard")

        notification_db: Notification | None = await self._notis_repo.get_record(
            idempotency_key=idempotency_key
        )

        if notification_db:
            sentry_logger.error(
                "Notification exists with the idempotency_key: {idempotency_key}",
                idempotency_key=idempotency_key,
            )
            raise NotificationExistsError(key=idempotency_key)

        current_depth: int = await channel.queue_depth(queue)

        if current_depth > self.SETTINGS.MAXIMUM_QUEUE_DEPTH:
            sentry_logger.error("Maximum depth reached for queue {queue}", queue=queue)
            raise ServiceUnavailable()

        webhook: WebhookEndpoint | None = await webhook_service._get_endpoint(
            curr_user.id, url
        )

        if not webhook:
            sentry_logger.info("Webhook endpoint not found with the url {url}", url=url)
            raise UrlNotFoundError(url=url)

        try:
            await self._notis_repo.add(entity=payload)
            await self._notis_repo.commit()
            sentry_logger.info(
                "Webhook Notification created successfully for user {email}",
                email=user_email,
            )

            notification_db: Notification | None = await self._notis_repo.get_record(
                idempotency_key=idempotency_key
            )

            deliver_webhook_task.appy_async(
                priority=5,
                kwargs={
                    "notification_id": notification_db.id,
                    "idempotency_key": idempotency_key,
                    "secret": webhook.secret,
                    "webhook_url": url,
                    "payload": payload.payload,
                }
            )

            return NotificationResponse.model_validate(notification_db)
        except Exception as e:
            await self._notis_repo.rollback()
            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while creating webhook notification for user {email}",
                email=user_email,
            )
            raise ServerError() from e

    async def get_notification(
        self, notification_id: UUID, curr_user: User
    ) -> NotificationResponse:
        user_email: str = self._get_user_email(curr_user)

        try:
            notification_db: Notification | None = await self._notis_repo.get_record(
                id=notification_id
            )

            if not notification_db:
                sentry_logger.error(
                    "Notification not found with id {id} for user {email}",
                    id=notification_id,
                    email=user_email,
                )
                raise NotificationNotFoundError(id=notification_id)

            return NotificationResponse.model_validate(notification_db)
        except Exception as e:
            if isinstance(e, NotificationNotFoundError):
                raise NotificationNotFoundError(id=notification_id)

            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while retrieving notification from db for user {email}",
                email=user_email,
            )
            raise ServerError() from e

    def get_digest_notifications(self) -> Sequence[Notification]:
        return self._notis_repo.get_sync_records(
            type="digest", status="pending", digest=True
        )

    def _get_notification(self, notification_id) -> Notification | None:
        return self._notis_repo.get_sync_record(id=notification_id)

    def update_notification(self, notification: Notification):
        try:
            self._notis_repo.sync_add(model=notification)
            self._notis_repo.sync_commit()
        except Exception as e:
            self._notis_repo.sync_rollback()
            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while updating notification record",
            )
            raise ServerError() from e
