from __future__ import annotations

from uuid import UUID
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    pass


class ServerError(AppException):
    """Internal Server error."""

    pass


class ServiceUnavailable(AppException):
    """Service unavailable temporarily"""

    pass


class TransientError(AppException):
    """Worker Transient error"""

    pass


class AuthenticationError(AppException):
    """User not authenticated."""

    pass


class AuthorizationError(AppException):
    """User not authorized"""

    pass


class CheckTimeoutError(AppException):
    """retry count exhausted"""

    pass


class UnverifiedEmailError(AppException):
    """unverified email provided"""

    pass


class UserExistsError(AppException):
    """User already exists"""

    def __init__(self, user_email: str):
        self.user_email = user_email


class UserNotFoundError(AppException):
    """User not found"""

    def __init__(self, user_email: str):
        self.user_email = user_email


class InvalidOtpError(AppException):
    """Invalid otp received"""

    pass


class CredentialError(AppException):
    """wrong credentials provided"""

    pass


class NotificationExistsError(AppException):
    """idempotency key exists"""

    def __init__(self, key: str):
        self.key = key


class NotificationNotFoundError(AppException):
    """Notification not found"""

    def __init__(self, id: str):
        self.id = id


class UrlNotFoundError(AppException):
    """Webhook endpoints not found"""

    def __init__(self, url: str = None, id: UUID = None):
        self.id = id
        self.url = url


class UrlExistsError(AppException):
    """webhook endpoint exists"""

    def __init__(self, url: str):
        self.url = url


def create_exception_handler(
    status_code: int, initial_detail: dict
) -> callable[[Request, AppException], JSONResponse]:
    async def exception_handler(request: Request, exc: AppException):
        message: str = initial_detail.get("message")
        initial_detail["message"] = message.format(**exc.__dict__)

        return JSONResponse(content=initial_detail, status_code=status_code)

    return exception_handler
