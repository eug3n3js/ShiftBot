from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.main.constants import AdminPanelAction
from ...constants import MainMenuAction


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="👥 Все пользователи",
                callback_data=AdminPanelAction.VIEW_ALL_USERS
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Активные пользователи",
                callback_data=AdminPanelAction.VIEW_ACTIVE_USERS
            )
        ],
        [
            InlineKeyboardButton(
                text="👑 Администраторы",
                callback_data=AdminPanelAction.VIEW_ADMIN_USERS
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Дать админ права",
                callback_data=AdminPanelAction.GRANT_ADMIN
            ),
            InlineKeyboardButton(
                text="➖ Забрать админ права",
                callback_data=AdminPanelAction.REVOKE_ADMIN
            )
        ],
        [
            InlineKeyboardButton(
                text="🔓 Активировать пользователя",
                callback_data=AdminPanelAction.ACTIVATE_USER
            ),
            InlineKeyboardButton(
                text="🔒 Деактивировать пользователя",
                callback_data=AdminPanelAction.DEACTIVATE_USER
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Отправить сообщение всем",
                callback_data=AdminPanelAction.SEND_MESSAGE_TO_ALL
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_admin_panel_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 Назад в админ-панель",
                callback_data=AdminPanelAction.BACK_TO_ADMIN_PANEL
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
