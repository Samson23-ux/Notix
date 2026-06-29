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


class NotificationResponse(NotificationBase):
    id: UUID
    status: NotificationStatus
    body: str | None
    subject: str | None
    recipient: EmailStr | None
    webhook_url: str | None
    payload: dict | None
    created_at: datetime
    delivered_at: datetime | None
    dead_lettered_at: datetime | None
    faliure_reason: str | None
    retry_count: int | None
