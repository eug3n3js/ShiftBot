from src.main.dao import MuteDAO
from src.main.utils.db_helper import DatabaseHelper


class MuteService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MuteService, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_helper: DatabaseHelper):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._mute_dao = MuteDAO(db_helper)

    @classmethod
    def initialize(cls, db_helper: DatabaseHelper):
        if cls._instance:
            raise RuntimeError("MuteService is already initialized. Use get_instance() to access it.")
        cls._instance = cls(db_helper)

    @classmethod
    def get_instance(cls) -> 'MuteService':
        if not cls._instance:
            raise RuntimeError("MuteService is not initialized. Call initialize() first.")
        return cls._instance

    async def mute_shift(self, user_id: int, shift_link: int) -> None:
        await self._mute_dao.create_mute(user_id, shift_link)

    async def get_batch_user_mutes(self, user_ids: list[int]) -> dict[int, set[int]]:
        user_mutes = await self._mute_dao.get_batch_user_mutes(user_ids)
        result = {}
        for user_id, mutes in user_mutes.items():
            result[user_id] = {mute.shift_link for mute in mutes}
        return result

    async def cleanup_expired_mutes(self) -> None:
        await self._mute_dao.cleanup_expired_mutes()

