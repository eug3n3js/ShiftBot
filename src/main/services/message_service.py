import os
import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from dotenv import load_dotenv

from src.main.dao import UserDAO


class MessageService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MessageService, cls).__new__(cls)
        return cls._instance

    def __init__(self, user_dao: UserDAO):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.user_dao = user_dao
            load_dotenv()
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not token:
                raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")
            self._bot = Bot(token=token)

    @classmethod
    def initialize(cls, user_dao):
        if cls._instance:
            raise RuntimeError("MessageService is already initialized. Use get_instance() to access it.")
        cls._instance = cls(user_dao)

    @classmethod
    def get_instance(cls) -> 'MessageService':
        if not cls._instance:
            raise RuntimeError("MessageService is not initialized. Call initialize() first.")
        return cls._instance

    async def send_message_all_users(self, message: str, protect_content: bool = False) -> None:
        users = await self.user_dao.get_users_with_active_access()
        for user in users:
            if user.tg_id:
                try:
                    await self._bot.send_message(chat_id=user.tg_id, text=message, protect_content=protect_content)
                except:
                    pass

    async def send_message_all_admin(self, message: str, protect_content: bool = False) -> None:
        admins = await self.user_dao.get_admins()
        for admin in admins:
            try:
                await self._bot.send_message(chat_id=admin.tg_id, text=message, protect_content=protect_content)
            except:
                pass

    async def send_message_specific_user(self, tg_id: int, message: str, keyboard: InlineKeyboardMarkup = None,
                                         protect_content: bool = True) -> None:
        if tg_id is None:
            return
        try:
            if keyboard:
                await self._bot.send_message(chat_id=tg_id, text=message,
                                             reply_markup=keyboard,
                                             protect_content=protect_content)
            else:
                await self._bot.send_message(chat_id=tg_id,
                                             text=message,
                                             protect_content=protect_content)
        except:
            pass
