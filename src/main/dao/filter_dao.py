from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from .base_dao import BaseDAO
from src.main.domain import Filter, FilterCompany, FilterLocation, FilterPosition
from src.main.utils.db_helper import DatabaseHelper
from src.main.schemas import (
    FilterBase
)
from ..schemas.filter import ListFieldBase


class FilterDAO(BaseDAO[Filter, FilterBase]):
    def __init__(self, db_helper: DatabaseHelper):
        super().__init__(db_helper, Filter, FilterBase)

    def _convert_to_schema(self, filter_obj: Filter) -> FilterBase:
        companies = []
        try:
            companies = [ListFieldBase(id=company.id, value=company.company) for company in filter_obj.companies]
        except:
            pass

        locations = []
        try:
            locations = [ListFieldBase(id=location.id, value=location.location) for location in filter_obj.locations]
        except:
            pass

        positions = []
        try:
            positions = [ListFieldBase(id=position.id, value=position.position) for position in filter_obj.positions]
        except:
            pass
        
        return FilterBase(
            id=filter_obj.id,
            user_id=filter_obj.user_id,
            is_black_list=filter_obj.is_black_list,
            is_and=filter_obj.is_and,
            companies=companies,
            locations=locations,
            positions=positions,
            longer=filter_obj.longer,
            shorter=filter_obj.shorter,
        )

    async def create_filter(self, filter_data: FilterBase) -> None:
        user_id = getattr(filter_data, 'user_id', None)
        if user_id is None:
            raise ValueError("user_id is required to create a filter")
            
        await self.create(
            user_id=user_id,
            is_black_list=filter_data.is_black_list or False,
        )

    async def update_filter(self, filter_id: int, filter_data: FilterBase) -> FilterBase | None:
        update_data = {}
        if filter_data.longer is not None:
            update_data['longer'] = filter_data.longer
        if filter_data.shorter is not None:
            update_data['shorter'] = filter_data.shorter
        if hasattr(filter_data, 'is_and') and filter_data.is_and is not None:
            update_data['is_and'] = filter_data.is_and
        
        filter_obj = await self.update(filter_id, **update_data)
        print(filter_obj)
        return filter_obj

    async def clear_longer(self, filter_id: int) -> None:
        await self.update(filter_id, longer=None)

    async def clear_shorter(self, filter_id: int) -> None:
        await self.update(filter_id, shorter=None)

    async def add_company(self, filter_id: int, company_data: str) -> None:
        async for session in self.db_helper.session_dependency():
            company_obj = FilterCompany(
                filter_id=filter_id,
                company=company_data
            )
            session.add(company_obj)
            await session.commit()
            await session.refresh(company_obj)

    async def add_location(self, filter_id: int, location_data: str) -> None:
        async for session in self.db_helper.session_dependency():
            location_obj = FilterLocation(
                filter_id=filter_id,
                location=location_data
            )
            session.add(location_obj)
            await session.commit()
            await session.refresh(location_obj)

    async def add_position(self, filter_id: int, position_data: str) -> None:
        async for session in self.db_helper.session_dependency():
            position_obj = FilterPosition(
                filter_id=filter_id,
                position=position_data
            )
            session.add(position_obj)
            await session.commit()
            await session.refresh(position_obj)

    async def remove_company(self, filter_id: int, company_id: int):
        async for session in self.db_helper.session_dependency():
            stmt = select(FilterCompany).where(
                and_(
                    FilterCompany.filter_id == filter_id,
                    FilterCompany.id == company_id
                )
            )
            result = await session.execute(stmt)
            company_obj = result.scalar_one_or_none()
            if company_obj:
                await session.delete(company_obj)
                await session.commit()

    async def remove_location(self, filter_id: int, location_id: int):
        async for session in self.db_helper.session_dependency():
            stmt = select(FilterLocation).where(
                and_(
                    FilterLocation.filter_id == filter_id,
                    FilterLocation.id == location_id
                )
            )
            result = await session.execute(stmt)
            location_obj = result.scalar_one_or_none()
            if location_obj:
                await session.delete(location_obj)
                await session.commit()

    async def remove_position(self, filter_id: int, position_id: int):
        async for session in self.db_helper.session_dependency():
            stmt = select(FilterPosition).where(
                and_(
                    FilterPosition.filter_id == filter_id,
                    FilterPosition.id == position_id
                )
            )
            result = await session.execute(stmt)
            position_obj = result.scalar_one_or_none()
            if position_obj:
                await session.delete(position_obj)
                await session.commit()

    async def get_batch_user_filters(self, user_ids: list[int]) -> dict[int, list[FilterBase]]:
        async for session in self.db_helper.session_dependency():
            stmt = select(Filter).options(
                selectinload(Filter.companies),
                selectinload(Filter.locations),
                selectinload(Filter.positions)
            ).where(Filter.user_id.in_(user_ids))
            result = await session.execute(stmt)
            filters = result.scalars().all()

            grouped_filters = {}
            for filter_obj in filters:
                user_id = filter_obj.user_id
                if user_id not in grouped_filters:
                    grouped_filters[user_id] = []
                grouped_filters[user_id].append(self._convert_to_schema(filter_obj))

            return grouped_filters
