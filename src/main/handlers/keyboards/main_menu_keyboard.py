from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.main.constants import MainMenuAction


def main_menu_keyboard(admin: bool = False) -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton(text="🔍 Фильтры", callback_data=MainMenuAction.FILTERS),
        InlineKeyboardButton(text="📋 Подписка", callback_data=MainMenuAction.SUBSCRIPTION),
    ]
    if admin:
        button_list.append(InlineKeyboardButton(text="👑 Админ-панель", callback_data=MainMenuAction.ADMIN_PANEL))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            button_list
        ]
    )
