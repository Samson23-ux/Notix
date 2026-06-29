from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


from app.api.models.notification import (
    NotificationType,
    NotificationPriority,
    NotificationStatus,
)


class NotificationBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    idempotency_key: str
    type: NotificationType
    priority: NotificationPriority = "medium"


class EmailNotification(NotificationBase):
    body: str
    subject: str
    recipient: EmailStr


class WebhookNotification(NotificationBase):
    webhook_url: str
    payload: dict


class NotificationResponse(BaseModel):
    id: UUID
    status: NotificationStatus
    created_at: datetime
    delivered_at: datetime
    dead_lettered_at: datetime
    faliure_reason: str
    retry_count: int


class EmailResponse(EmailNotification, NotificationResponse):
    pass


class WebhookResponse(WebhookNotification, NotificationResponse):
    pass
