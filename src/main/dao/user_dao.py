from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .base_dao import BaseDAO
from src.main.domain import User
from src.main.utils.db_helper import DatabaseHelper
from src.main.schemas import UserBase


class UserDAO(BaseDAO[User, UserBase]):
    def __init__(self, db_helper: DatabaseHelper):
        super().__init__(db_helper, User, UserBase)

    def _convert_to_schema(self, user_obj: User) -> UserBase:
        return UserBase(
            id=user_obj.id,
            tg_id=user_obj.tg_id,
            is_admin=user_obj.is_admin,
            access_ends=user_obj.access_ends,
            created_at=getattr(user_obj, 'created_at', None)
        )

    async def get_by_tg_id(self, tg_id: int) -> UserBase | None:
        async for session in self.db_helper.session_dependency():
            stmt = select(User).where(User.tg_id == tg_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return self._convert_to_schema(user)
            return None

    async def get_admins(self) -> List[UserBase]:
        async for session in self.db_helper.session_dependency():
            stmt = select(User).where(User.is_admin)
            result = await session.execute(stmt)
            users = result.scalars().all()
            return [self._convert_to_schema(user) for user in users]

    async def create_user(self, user_data: UserBase) -> UserBase:
        try:
            user_obj = await self.create(
                tg_id=user_data.tg_id,
                is_admin=user_data.is_admin or False
            )
            return user_obj
        except IntegrityError:
            raise ValueError("Пользователь с таким Telegram ID уже существует")

    async def update_user(self, user_id: int, user_data: UserBase) -> Optional[UserBase]:
        update_data = {}
        if user_data.is_admin is not None:
            update_data['is_admin'] = user_data.is_admin
        if user_data.access_ends is not None:
            update_data['access_ends'] = user_data.access_ends
        
        try:
            return await self.update(user_id, **update_data)
        except IntegrityError:
            raise ValueError("Пользователь с таким Telegram ID уже существует")

    async def clear_access_ends(self, user_id: int) -> None:
        await self.update(user_id, access_ends=None)

    async def get_users_with_active_access(self) -> list[UserBase]:
        async for session in self.db_helper.session_dependency():
            current_time = datetime.now()
            stmt = select(User).where(User.access_ends > current_time)
            result = await session.execute(stmt)
            users = result.scalars().all()
            return [self._convert_to_schema(user) for user in users]
