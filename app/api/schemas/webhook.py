from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WebhookBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    endpoint: str


class Webhook(WebhookBase):
    pass


class WebhookInDB(WebhookBase):
    user_id: UUID
    secret: str


class WebhookResponse(WebhookBase):
    id: UUID
    user_id: UUID
    secret: str
    created_at: datetime
