from datetime import timedelta

from src.main.dao import UserDAO, FilterDAO
from src.main.schemas import UserBase, FilterBase


class UserService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UserService, cls).__new__(cls)
        return cls._instance

    def __init__(self, user_dao: UserDAO, filter_dao: FilterDAO):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.user_dao = user_dao
            self.filter_dao = filter_dao
            self.instant_admin = 701565078

    @classmethod
    def initialize(cls, user_dao, filter_dao):
        if cls._instance:
            raise RuntimeError("UserService is already initialized. Use get_instance() to access it.")
        cls._instance = cls(user_dao, filter_dao)

    @classmethod
    def get_instance(cls) -> 'UserService':
        if not cls._instance:
            raise RuntimeError("UserService is not initialized. Call initialize() first.")
        return cls._instance

    async def get_all_users(self) -> list[UserBase]:
        return await self.user_dao.get_all()

    async def get_admins(self) -> list[UserBase]:
        return await self.user_dao.get_admins()

    async def get_active_users(self) -> list[UserBase]:
        return await self.user_dao.get_users_with_active_access()

    async def get_user_by_tg_id(self, tg_id: int) -> UserBase | None:
        return await self.user_dao.get_by_tg_id(tg_id)

    async def create_user(self, user: UserBase) -> None:
        user = await self.user_dao.create_user(user)
        await self.filter_dao.create_filter(FilterBase(user_id=user.id, is_black_list=True))
        await self.filter_dao.create_filter(FilterBase(user_id=user.id, is_black_list=False))

    async def grant_admin(self, user_id: int) -> None:
        await self.user_dao.update_user(user_id, UserBase(is_admin=True))

    async def revoke_admin(self, user_id: int) -> None:
        user = await self.user_dao.get_by_id(user_id)
        await self.user_dao.update_user(user_id, UserBase(is_admin=False))

    async def activate(self, user_id: int, time_d: timedelta) -> None:
        if not self.instant_admin:
            return
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            return
        from datetime import datetime
        now = datetime.now()
        base_time = user.access_ends if (user.access_ends and user.access_ends > now) else now
        new_until = base_time + time_d
        await self.user_dao.update_user(user.id, UserBase(access_ends=new_until))

    async def get_user_filters(self, user_id: int) -> list[FilterBase]:
        grouped = await self.filter_dao.get_batch_user_filters([user_id])
        return grouped.get(user_id, [])

    async def deactivate(self, user_id: int) -> None:
        await self.user_dao.clear_access_ends(user_id)

    async def update_filter(self, shift_filter: FilterBase) -> None:
        await self.filter_dao.update_filter(shift_filter.id, shift_filter)

    async def clear_filter_longer(self, filter_id: int) -> None:
        await self.filter_dao.clear_longer(filter_id)

    async def clear_filter_shorter(self, filter_id: int) -> None:
        await self.filter_dao.clear_shorter(filter_id)

    async def add_filter_company(self, filter_id: int, company: str) -> None:
        await self.filter_dao.add_company(filter_id, company)

    async def remove_filter_company(self, filter_id: int, company_id: int) -> None:
        await self.filter_dao.remove_company(filter_id, company_id)

    async def add_filter_location(self, filter_id: int, location: str) -> None:
        await self.filter_dao.add_location(filter_id, location)

    async def remove_filter_location(self, filter_id: int, location_id: int) -> None:
        await self.filter_dao.remove_location(filter_id, location_id)

    async def add_filter_position(self, filter_id: int, position: str) -> None:
        await self.filter_dao.add_position(filter_id, position)

    async def remove_filter_position(self, filter_id: int, position_id: int) -> None:
        await self.filter_dao.remove_position(filter_id, position_id)

    def check_admin(self, user: UserBase) -> bool:
        if user.is_admin or user.tg_id == self.instant_admin:
            return True
        return False

