from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ApiKeyBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

    key: str


class ApiKey(ApiKeyBase):
    user_id: UUID


class ApiKeyResponse(ApiKeyBase):
    id: UUID
    user_id: UUID
    created_at: datetime
