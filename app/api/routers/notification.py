from uuid import UUID
from fastapi import APIRouter, Request


from app.deps import NotificationServiceDep
from app.api.schemas.response import SuccessResponse
from app.api.schemas.notification import (
    EmailResponse,
    WebhookResponse,
    EmailNotification,
    WebhookNotification,
)

router = APIRouter()


@router.post(
    "/notifications",
    status_code=202,
    response_model=SuccessResponse[EmailResponse],
    description="Create an email notification",
)
async def create_notification(
    request: Request,
    notification_payload: EmailNotification,
    notification_service: NotificationServiceDep,
):
    pass


@router.post(
    "/notifications/webhook",
    status_code=202,
    response_model=SuccessResponse[WebhookResponse],
    description="Create a webhook notification",
)
async def create_webhook_notification(
    request: Request,
    webhook_payload: WebhookNotification,
    notification_service: NotificationServiceDep,
):
    pass


@router.get(
    "/notifications/{id}",
    status_code=200,
    response_model=SuccessResponse[EmailResponse | WebhookResponse],
    description="Get a notification to check status and details",
)
async def get_notification(
    id: UUID, request: Request, notification_service: NotificationServiceDep
):
    pass
