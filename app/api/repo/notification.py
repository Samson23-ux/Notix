from typing import Any
from datetime import datetime, timezone, timedelta


from app.api.repo.base import BaseRepository
from app.api.models.notification import Notification
from app.api.schemas.notification import NotificationBase


class NotificationRepository(BaseRepository[NotificationBase, Notification]):
    model = Notification

    def _get_filters(self, **filters) -> list[Any]:
        filter_conditions = []

        if "id" in filters:
            filter_conditions.append(self.model.id == filters["id"])
        if "idempotency_key" in filters:
            filter_conditions.append(self.model.idempotency_key == filters["idempotency_key"])
        if "type" in filters:
            filter_conditions.append(self.model.type == filters["type"])
        if "status" in filters:
            filter_conditions.append(self.model.status == filters["status"])
        if "priority" in filters:
            filter_conditions.append(self.model.priority == filters["priority"])
        if "digest" in filters:
            cutoff: datetime = datetime.now(timezone.utc) - timedelta(hours=1)
            filter_conditions.append(self.model.created_at <= cutoff)

    def _entity_to_model(self, entity: NotificationBase) -> Notification:
        return Notification(**entity.model_dump())
