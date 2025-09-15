from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from .keyboards import main_menu_keyboard
from ..constants import MainMenuAction
from ..schemas import UserBase
from ..services.user_service import UserService
from ..utils.username_utils import get_username_from_chat_id

base_router = Router(name="base")


@base_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(message.chat.id)
    if not user:
        await user_service.create_user(UserBase(tg_id=message.chat.id))
    user = await user_service.get_user_by_tg_id(message.chat.id)
    await message.answer(
        "Привет! Это базовый бот. Используй кнопки ниже.",
        reply_markup=main_menu_keyboard(user_service.check_admin(user)),
    )


@base_router.callback_query(F.data == MainMenuAction.MAIN_MENU)
async def back_to_main_menu(callback: CallbackQuery) -> None:
    user_service = UserService.get_instance()
    await callback.answer()
    await callback.message.edit_text(
        "Привет! Это базовый бот. Используй кнопки ниже.",
        reply_markup=main_menu_keyboard(user_service.check_admin(await user_service.get_user_by_tg_id(callback.message.chat.id))),
    )


@base_router.callback_query(F.data == MainMenuAction.SUBSCRIPTION)
async def on_subscription_info(callback: CallbackQuery) -> None:
    await callback.answer()
    
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text(
            "❌ Пользователь не найден",
            reply_markup=main_menu_keyboard(False)
        )
        return
    
    admin_username = "@parashkinoff"
    
    current_time = datetime.now()
    is_active = user.access_ends and user.access_ends > current_time
    
    if is_active:
        end_date = user.access_ends.strftime("%d.%m.%Y %H:%M")
        message_text = f"✅ Ваша подписка активна\n\n"
        message_text += f"📅 Действует до: {end_date}\n\n"
        message_text += f"⏰ Осталось времени: {_format_time_remaining(user.access_ends, current_time)}\n\n"
        message_text += f"💬 Для продления обратитесь к администратору: {admin_username}"
    else:
        message_text = f"❌ Ваша подписка неактивна\n\n"
        message_text += f"💬 Для активации обратитесь к администратору: {admin_username}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=MainMenuAction.MAIN_MENU)]
        ]
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard
    )


def _format_time_remaining(end_date: datetime, current_time: datetime) -> str:
    """Форматирует оставшееся время до окончания подписки"""
    remaining = end_date - current_time
    
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} дн. {hours} ч. {minutes} мин."
    elif hours > 0:
        return f"{hours} ч. {minutes} мин."
    else:
        return f"{minutes} мин."

