from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Any, Optional


from app.api.models.base import Base


Entity = TypeVar("Entity", bound=BaseModel)
SqlalchemyModel = TypeVar("SqlAlchemyModel", bound=Base)


class BaseRepository(ABC, Generic[Entity, SqlalchemyModel]):
    def __init__(
        self, async_session: AsyncSession = None, sync_session: Session = None
    ):
        self._sync_session = sync_session
        self._async_session = async_session

    def add(
        self, entity: Optional[Entity] = None, model: Optional[SqlalchemyModel] = None
    ):
        if not model:
            model: SqlalchemyModel = self._entity_to_model(entity)
        self._async_session.add(model)

    async def flush(self):
        await self._async_session.flush()

    async def refresh(self, model: SqlalchemyModel):
        await self._async_session.refresh(model)

    async def commit(self):
        await self._async_session.commit()

    async def rollback(self):
        await self._async_session.rollback()

    async def aclose(self):
        await self._async_session.aclose()

    async def delete(self, model: SqlalchemyModel):
        await self._async_session.delete(model)
        await self._async_session.flush()

    async def get_record(
        self, **filters
    ) -> SqlalchemyModel | None:
        filter_conditions: list[Any] = self._get_filters(**filters)

        res = await self._async_session.execute(select(self.model).where(*filter_conditions))
        return res.scalar()

    @abstractmethod
    def _entity_to_model(self, entity: Entity) -> SqlalchemyModel:
        raise NotImplementedError("Subclasses must implement _entity_to_model method")

    @abstractmethod
    def _get_filters(self, **filters) -> list[Any]:
        return []

    # sync db queries
    def sync_add(
        self, entity: Optional[Entity] = None, model: Optional[SqlalchemyModel] = None
    ):
        if not model:
            model: SqlalchemyModel = self._entity_to_model(entity)
        self._sync_session.add(model)

    def sync_flush(self):
        self._sync_session.flush()

    def sync_refresh(self, model: SqlalchemyModel):
        self._sync_session.refresh(model)

    def sync_commit(self):
        self._sync_session.commit()

    def sync_rollback(self):
        self._sync_session.rollback()

    def sync_delete(self, model: SqlalchemyModel):
        self._sync_session.delete(model)
        self._sync_session.flush()

    def close(self):
        self._sync_session.close()
