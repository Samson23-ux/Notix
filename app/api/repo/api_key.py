from typing import Any


from app.api.models.api_key import ApiKey
from app.api.schemas.api_key import ApiKeyBase
from app.api.repo.base import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKeyBase, ApiKey]):
    model = ApiKey

    @staticmethod
    def _entity_to_model(entity: ApiKeyBase) -> model:
        return ApiKey(**entity.model_dump())

    def _get_filters(self, **filters) -> list[Any]:
        filter_conditions = []

        if "key" in filters:
            filter_conditions.append(self.model.key == filters["key"])
        if "user_id" in filters:
            filter_conditions.append(self.model.user_id == filters["user_id"])

        return filter_conditions

    def _get_sort_fields(self, sort: str) -> list[Any]:
        sortable_fields: dict = {"created_at": self.model.created_at}
        return [sortable_fields.get(sort, self.model.created_at)]
