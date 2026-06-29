from uuid import UUID
from fastapi import APIRouter, Request


from app.api.schemas.response import SuccessResponse
from app.deps import NotificationServiceDep, EvenetChannelDep, CurrentActiveUser
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
    notification_payload: EmailNotification,
    notification_service: NotificationServiceDep,
):
    notification: NotificationResponse = (
        await notification_service.create_email_notification(
            event_channel, curr_user, notification_payload
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
    webhook_payload: WebhookNotification,
    notification_service: NotificationServiceDep,
):
    notification: NotificationResponse = (
        await notification_service.create_webhook_notification(
            event_channel, curr_user, webhook_payload
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
