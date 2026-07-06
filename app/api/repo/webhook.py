from typing import Any


from app.api.repo.base import BaseRepository
from app.api.schemas.webhook import WebhookBase
from app.api.models.webhook import WebhookEndpoint


class WebhookRepository(BaseRepository[WebhookBase, WebhookEndpoint]):
    model = WebhookEndpoint

    @staticmethod
    def _entity_to_model(entity: WebhookBase) -> WebhookEndpoint:
        return WebhookEndpoint(**entity.model_dump())

    def _get_filters(self, **filters) -> list[Any]:
        filter_conditions = []

        if "id" in filters:
            filter_conditions.append(self.model.id == filters["id"])
        if "user_id" in filters:
            filter_conditions.append(self.model.user_id == filters["user_id"])
        if "endpoint" in filters:
            filter_conditions.append(self.model.endpoint == filters["endpoint"])
        return filter_conditions
