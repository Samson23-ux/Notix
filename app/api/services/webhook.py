import secrets
import sentry_sdk
from uuid import UUID
import sentry_sdk.logger as sentry_logger


from app.util import get_user_email
from app.api.models.user import User
from app.api.models.webhook import WebhookEndpoint
from app.api.repo.webhook import WebhookRepository
from app.api.schemas.webhook import Webhook, WebhookInDB, WebhookResponse
from app.core.exceptions import ServerError, UrlExistsError, UrlNotFoundError


class WebhookService:
    def __init__(self, webhook_repo: WebhookRepository):
        self._webhook_repo = webhook_repo

    async def _get_endpoint(self, user_id: UUID, url: str) -> WebhookEndpoint | None:
        return await self._webhook_repo.get_record(user_id=user_id, endpoint=url)

    async def create_endpoint(
        self, curr_user: User, payload: Webhook
    ) -> WebhookResponse:
        url: str = payload.endpoint
        user_id: UUID = curr_user.id
        user_email: str = get_user_email(curr_user)

        webhook_exists: WebhookEndpoint | None = await self._webhook_repo.get_record(
            user_id=user_id, endpoint=url
        )

        if webhook_exists:
            sentry_logger.error(
                "Webhook endpoint {url} already exists in db by user {email}",
                email=user_email,
                url=url,
            )
            raise UrlExistsError(url=url)

        try:
            webhook_db: WebhookInDB = WebhookInDB(
                user_id=user_id,
                secret=secrets.token_urlsafe(32),
                **payload.model_dump(),
            )
            self._webhook_repo.add(entity=webhook_db)
            await self._webhook_repo.commit()

            webhook: WebhookEndpoint | None = await self._webhook_repo.get_record(
                user_id=user_id, endpoint=url
            )

            sentry_logger.info(
                "Webhook endpoint created for user {email}", email=user_email
            )
            return WebhookResponse.model_validate(webhook)
        except Exception as e:
            await self._webhook_repo.rollback()

            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while creating webhook endpoint for user {email}",
                email=user_email,
            )
            raise ServerError() from e

    async def delete_endpoint(self, curr_user: User, endpoint_id: UUID):
        user_id: UUID = curr_user.id
        user_email: str = get_user_email(curr_user)

        try:
            webhook: WebhookEndpoint | None = await self._webhook_repo.get_record(
                user_id=user_id, id=endpoint_id
            )

            if not webhook:
                sentry_logger.info(
                    "Webhook endpoint not found with the id {id}", id=endpoint_id
                )
                raise UrlNotFoundError(id=endpoint_id)

            await self._webhook_repo.delete(model=webhook)
            await self._webhook_repo.commit()
        except Exception as e:
            await self._webhook_repo.rollback()
            if isinstance(e, UrlNotFoundError):
                raise UrlNotFoundError() from e

            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while deleting webhook endpoint for user {email}",
                email=user_email,
            )
            raise ServerError() from e
