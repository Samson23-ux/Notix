from uuid import UUID
from fastapi import APIRouter, Request


from app.api.schemas.response import SuccessResponse
from app.deps import (
    ApiKeyServiceDep,
    EvenetChannelDep,
    CurrentActiveUser,
    WebhookServiceDep,
    NotificationServiceDep,
)
from app.api.schemas.notification import (
    EmailNotification,
    WebhookNotification,
    NotificationResponse,
)

router = APIRouter()


@router.post(
    "/notifications",
    status_code=202,
    response_model=SuccessResponse[NotificationResponse],
    description="Create an email notification",
)
async def create_notification(
    request: Request,
    curr_user: CurrentActiveUser,
    event_channel: EvenetChannelDep,
    api_key_service: ApiKeyServiceDep,
    notification_payload: EmailNotification,
    notification_service: NotificationServiceDep,
):
    api_key: str = request.headers.get("api_key")
    notification: NotificationResponse = (
        await notification_service.create_email_notification(
            api_key, curr_user, event_channel, notification_payload, api_key_service
        )
    )
    return SuccessResponse(
        message="Email Notification created successfully", data=notification
    )


@router.post(
    "/notifications/webhook",
    status_code=202,
    response_model=SuccessResponse[NotificationResponse],
    description="Create a webhook notification",
)
async def create_webhook_notification(
    request: Request,
    curr_user: CurrentActiveUser,
    event_channel: EvenetChannelDep,
    api_key_service: ApiKeyServiceDep,
    webhook_service: WebhookServiceDep,
    webhook_payload: WebhookNotification,
    notification_service: NotificationServiceDep,
):
    api_key: str = request.headers.get("api_key")
    notification: NotificationResponse = (
        await notification_service.create_webhook_notification(
            api_key,
            curr_user,
            event_channel,
            webhook_payload,
            api_key_service,
            webhook_service,
        )
    )
    return SuccessResponse(
        message="Webhook Notification created successfully", data=notification
    )


@router.get(
    "/notifications/{id}",
    status_code=200,
    response_model=SuccessResponse[NotificationResponse],
    description="Get a notification to check status and details",
)
async def get_notification(
    id: UUID,
    request: Request,
    curr_user: CurrentActiveUser,
    notification_service: NotificationServiceDep,
):
    notification: NotificationResponse = await notification_service.get_notification(
        id, curr_user
    )
    return SuccessResponse(
        message="Notification retrieved successfully", data=notification
    )
