import secrets
import sentry_sdk
from uuid import UUID
from sqlalchemy import Sequence
import sentry_sdk.logger as sentry_logger


from app.util import get_user_email
from app.api.models.user import User
from app.api.models.api_key import ApiKey
from app.api.repo.api_key import ApiKeyRepository
from app.api.schemas.api_key import ApiKey as ApiKeySchema, ApiKeyResponse
from app.core.exceptions import ServerError, ApiKeyNotFoundError, ApiKeysNotFoundError


class ApiKeyService:
    def __init__(self, api_key_repo: ApiKeyRepository):
        self._api_key_repo = api_key_repo

    async def create_api_key(self, curr_user: User) -> ApiKeyResponse:
        user_id: UUID = curr_user.id
        user_email: str = get_user_email(curr_user)

        try:
            key: str = secrets.token_urlsafe(32)
            api_key: ApiKeySchema = ApiKeySchema(key=key, user_id=user_id)
            self._api_key_repo.add(entity=api_key)
            await self._api_key_repo.commit()

            api_key_db: ApiKey = await self._api_key_repo.get_record(
                key=key, user_id=user_id
            )
            return ApiKeyResponse.model_validate(api_key_db)
        except Exception as e:
            await self._api_key_repo.rollback()
            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while creating api key for user {email}",
                email=user_email,
            )
            raise ServerError() from e

    async def get_all_api_keys(
        self,
        curr_user: User,
        sort: str | None,
        order: str,
        cursor: str | None,
        limit: int,
    ) -> tuple:
        user_email: str = get_user_email(curr_user)

        try:
            data: dict = await self._api_key_repo.get_records(
                sort, order, cursor, limit, user_id=curr_user.id, is_valid=True
            )

            cursor: str = data.get("cursor")
            api_keys: Sequence[ApiKey] = data.get("data")

            if not api_keys:
                sentry_logger.error("Api Keys for user {email}", email=user_email)
                raise ApiKeysNotFoundError()

            api_keys_out: list[ApiKeyResponse] = []
            for api_key in api_keys:
                api_keys_out.append(ApiKeyResponse.model_validate(api_key))

            sentry_logger.info("Api Keys retrieved for user {email}", email=user_email)
            return api_keys_out, cursor
        except Exception as e:
            if isinstance(e, ApiKeysNotFoundError):
                raise ApiKeysNotFoundError()

            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while retrieving api keys for user {email}",
                email=user_email,
            )
            raise ServerError() from e

    async def get_api_key(self, curr_user: User, key: str) -> ApiKeyResponse:
        user_id: UUID = curr_user.id
        user_email: str = get_user_email(curr_user)

        try:
            api_key_db: ApiKey = await self._api_key_repo.get_record(
                key=key, user_id=user_id
            )

            if not api_key_db:
                sentry_logger.error(
                    "No Api Key found with the key {key} for user {email}",
                    key=key,
                    email=user_email,
                )
                raise ApiKeyNotFoundError(key=key)
            return ApiKeyResponse.model_validate(api_key_db)
        except Exception as e:
            if isinstance(e, ApiKeyNotFoundError):
                raise ApiKeyNotFoundError(key=key)

            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while retrieving api key for user {email}",
                email=user_email,
            )
            raise ServerError() from e

    async def _get_api_key(self, user_id: UUID, key: str | None) -> ApiKey | None:
        return await self._api_key_repo.get_record(key=key, user_id=user_id)

    async def delete_api_key(self, curr_user: User, key: str):
        user_id: UUID = curr_user.id
        user_email: str = get_user_email(curr_user)

        api_key_db: ApiKey = await self._api_key_repo.get_record(
            key=key, user_id=user_id
        )

        if not api_key_db:
            sentry_logger.error(
                "No Api Key found with the key {key} for user {email}",
                key=key,
                email=user_email,
            )
            raise ApiKeyNotFoundError(key=key)

        try:
            await self._api_key_repo.delete(model=api_key_db)
            await self._api_key_repo.commit()
        except Exception as e:
            await self._api_key_repo.rollback()

            sentry_sdk.capture_exception(e)
            sentry_logger.error(
                "Error occured while deleting api key for user {email}",
                email=user_email,
            )
            raise ServerError() from e
