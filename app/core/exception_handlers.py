from fastapi import FastAPI


from app.core.exceptions import (
    create_exception_handler,
    ServerError,
    AuthenticationError,
    UserExistsError,
    UrlExistsError,
    InvalidOtpError,
    UserNotFoundError,
    CredentialError,
    UrlNotFoundError,
    AuthorizationError,
    CheckTimeoutError,
    UnverifiedEmailError,
    ServiceUnavailable,
    NotificationExistsError,
    NotificationNotFoundError,
    ApiKeyMissingError,
    ApiKeyNotFoundError,
    ApiKeysNotFoundError,
)


class ExceptionHandler:
    def __init__(self, app: FastAPI):
        self._app = app

    def add_handlers(self):
        self._app.add_exception_handler(
            ServerError,
            create_exception_handler(
                status_code=500,
                initial_detail={
                    "status": "error",
                    "message": "Oops! Something went wrong.",
                },
            ),
        )

        self._app.add_exception_handler(
            ServiceUnavailable,
            create_exception_handler(
                status_code=503,
                initial_detail={
                    "status": "error",
                    "message": "Service unavailble! Try again after five minutes",
                },
            ),
        )

        self._app.add_exception_handler(
            AuthenticationError,
            create_exception_handler(
                status_code=401,
                initial_detail={
                    "status": "error",
                    "message": "User not authenticated.",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=AuthorizationError,
            handler=create_exception_handler(
                status_code=403,
                initial_detail={
                    "status": "error",
                    "message": "User is not authorized to make the requested action",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=UserExistsError,
            handler=create_exception_handler(
                status_code=409,
                initial_detail={
                    "status": "error",
                    "message": "User already exists with the provided email {user_email}",
                },
            ),
        )

        self._app.add_exception_handler(
            InvalidOtpError,
            create_exception_handler(
                initial_detail={
                    "status": "error",
                    "message": "Invalid otp received",
                },
                status_code=400,
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=UserNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "User not found with email {user_email}",
                },
            ),
        )

        self._app.add_exception_handler(
            CredentialError,
            create_exception_handler(
                initial_detail={
                    "status": "error",
                    "message": "Invalid credentials!",
                },
                status_code=400,
            ),
        )

        self._app.add_exception_handler(
            CheckTimeoutError,
            create_exception_handler(
                initial_detail={
                    "status": "error",
                    "message": "Ensure the device is connected to the internet",
                },
                status_code=408,
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=UnverifiedEmailError,
            handler=create_exception_handler(
                status_code=400,
                initial_detail={
                    "status": "error",
                    "message": "Email not verified",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=NotificationExistsError,
            handler=create_exception_handler(
                status_code=409,
                initial_detail={
                    "status": "error",
                    "message": "Notification exists with the idempotency key {key}",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=NotificationNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "Notification not found with id {id}",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=UrlNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "Webhook endpoint not found with url {url} or id {id}",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=UrlExistsError,
            handler=create_exception_handler(
                status_code=409,
                initial_detail={
                    "status": "error",
                    "message": "Webhook endponts exists with the url {url}",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=ApiKeysNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "No Api Key found at the moment",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=ApiKeyNotFoundError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "No Api Key found with the key {key}",
                },
            ),
        )

        self._app.add_exception_handler(
            exc_class_or_status_code=ApiKeyMissingError,
            handler=create_exception_handler(
                status_code=404,
                initial_detail={
                    "status": "error",
                    "message": "Api Key missing!",
                },
            ),
        )
