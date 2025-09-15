from sqlalchemy import select, delete
from datetime import datetime, timedelta

from .base_dao import BaseDAO
from src.main.domain import Mute
from src.main.schemas import MuteBase
from src.main.utils.db_helper import DatabaseHelper


class MuteDAO(BaseDAO[Mute, MuteBase]):
    def __init__(self, db_helper: DatabaseHelper):
        super().__init__(db_helper, Mute, MuteBase)

    def _convert_to_schema(self, mute_obj: Mute) -> MuteBase:
        return MuteBase(
            id=mute_obj.id,
            user_id=mute_obj.user_id,
            shift_link=mute_obj.shift_link,
            created_at=mute_obj.created_at
        )

    async def create_mute(self, user_id: int, shift_link: int) -> None:
        await self.create(
            user_id=user_id,
            shift_link=shift_link,
            created_at=datetime.utcnow()
        )

    async def get_batch_user_mutes(self, user_ids: list[int]) -> dict[int, list[MuteBase]]:
        async for session in self.db_helper.session_dependency():
            result = await session.execute(
                select(Mute).where(Mute.user_id.in_(user_ids))
            )
            mutes = result.scalars().all()
            
            user_mutes = {}
            for mute in mutes:
                if mute.user_id not in user_mutes:
                    user_mutes[mute.user_id] = []
                user_mutes[mute.user_id].append(self._convert_to_schema(mute))
            
            return user_mutes

    async def cleanup_expired_mutes(self) -> None:
        cutoff_time = datetime.utcnow()
        async for session in self.db_helper.session_dependency():
            await session.execute(
                delete(Mute).where(Mute.created_at < cutoff_time)
            )
            await session.commit()
