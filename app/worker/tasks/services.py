from httpx import Client


from app.core.config import get_settings
from app.api.repo.otp import OtpRepository
from app.api.services.otp import OtpService
from app.api.services.request import Request
from app.api.repo.user import UserRepository
from app.api.services.user import UserService
from app.api.repo.email import EmailRepository
from app.api.repo.redis import RedisRepository
from app.api.services.email import EmailService
from app.api.services.channel import EventChannel
from app.worker.db import get_db_session, get_redis_client
from app.api.repo.notification import NotificationRepository
from app.api.services.notification import NotificationService

SETTINGS = get_settings()


def get_email_service() -> EmailService:
    session = get_db_session()

    email_service: EmailService = EmailService(
        email_repo=EmailRepository(sync_session=session)
    )

    return email_service


def get_notification_service() -> NotificationService:
    session = get_db_session()

    email_service: NotificationService = NotificationService(
        email_repo=NotificationRepository(sync_session=session)
    )

    return email_service


def get_user_service() -> UserService:
    session = get_db_session()
    user_service: UserService = UserService(
        user_repo=UserRepository(sync_session=session)
    )
    return user_service


def get_otp_service() -> OtpService:
    session = get_db_session()
    otp_service: OtpService = OtpService(otp_repo=OtpRepository(sync_session=session))
    return otp_service


def get_request_service() -> Request:
    return Request(sync_client=Client(timeout=10.0))


def get_redis_repo() -> RedisRepository:
    return RedisRepository(sync_redis=get_redis_client())


def get_event_channel() -> EventChannel:
    return EventChannel(SETTINGS.BROKER_URL)
