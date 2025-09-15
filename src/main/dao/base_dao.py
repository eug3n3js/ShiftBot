from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type
from sqlalchemy import select, delete

from src.main.domain import Base
from ..utils.db_helper import DatabaseHelper

T = TypeVar('T', bound=Base)
S = TypeVar('S')


class BaseDAO(ABC, Generic[T, S]):
    def __init__(self, db_helper: DatabaseHelper, model_class: Type[T], schema_class: Type[S]):
        self.db_helper = db_helper
        self.model_class = model_class
        self.schema_class = schema_class

    async def create(self, **kwargs) -> S:
        async for session in self.db_helper.session_dependency():
            obj = self.model_class(**kwargs)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            # Convert to schema within the session context to avoid lazy loading issues
            schema_obj = self._convert_to_schema(obj)
            return schema_obj

    async def get_by_id(self, obj_id: int) -> S | None:
        async for session in self.db_helper.session_dependency():
            obj = await session.get(self.model_class, obj_id)
            if obj:
                return self._convert_to_schema(obj)
            return None

    async def get_all(self) -> list[S]:
        async for session in self.db_helper.session_dependency():
            stmt = select(self.model_class)
            result = await session.execute(stmt)
            objects = result.scalars().all()
            return [self._convert_to_schema(obj) for obj in objects]

    async def update(self, obj_id: int, **kwargs) -> S | None:
        async for session in self.db_helper.session_dependency():
            obj = await session.get(self.model_class, obj_id)
            if obj:
                for key, value in kwargs.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                await session.commit()
                await session.refresh(obj)
            return self._convert_to_schema(obj)

    async def delete(self, obj_id: int) -> None:
        async for session in self.db_helper.session_dependency():
            await session.execute(delete(T).where(T.id == obj_id))

    async def exists(self, obj_id: int) -> bool:
        async for session in self.db_helper.session_dependency():
            obj = await session.get(self.model_class, obj_id)
            return obj is not None

    @abstractmethod
    def _convert_to_schema(self, obj: T) -> S:
        pass
