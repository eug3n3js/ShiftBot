from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.main.constants import (
    MainMenuAction,
    FilterAction,
    ModifyFilterAction,
    AddFilterAction,
    RemoveFilterAction,
    CallbackWithIdAction,
    POSITION_LIST
)
from src.main.schemas import ListFieldBase


def filters_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Белый список", callback_data=FilterAction.WHITE_LIST),
                InlineKeyboardButton(text="❌ Чёрный список", callback_data=FilterAction.BLACK_LIST),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=MainMenuAction.MAIN_MENU),
            ],
        ]
    )


def filter_manage_keyboard(list_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить правило", callback_data=ModifyFilterAction.ADD_RULE + list_type),
                InlineKeyboardButton(text="🗑 Удалить правило", callback_data=ModifyFilterAction.DELETE_RULE + list_type),
            ],
            [
                InlineKeyboardButton(text="🔧 Настроить логику", callback_data=ModifyFilterAction.SET_LOGIC + list_type),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=FilterAction.FILTERS_MENU),
            ],
        ]
    )


def add_rule_menu_keyboard(list_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏢 Компания", callback_data=AddFilterAction.ADD_COMPANY + list_type),
                InlineKeyboardButton(text="📍 Локация", callback_data=AddFilterAction.ADD_LOCATION + list_type),
            ],
            [
                InlineKeyboardButton(text="👷 Позиция", callback_data=AddFilterAction.ADD_POSITION + list_type),
            ],
            [
                InlineKeyboardButton(text="⏱ Мин. длительность", callback_data=AddFilterAction.ADD_LONGER + list_type),
                InlineKeyboardButton(text="⏱ Макс. длительность", callback_data=AddFilterAction.ADD_SHORTER + list_type),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=ModifyFilterAction.MODIFY_MENU + list_type),
            ],
        ]
    )


def remove_rule_menu_keyboard(list_type: str) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏢 Удалить компанию", callback_data=RemoveFilterAction.REMOVE_COMPANY + list_type),
                InlineKeyboardButton(text="📍 Удалить локацию", callback_data=RemoveFilterAction.REMOVE_LOCATION + list_type),
            ],
            [
                InlineKeyboardButton(text="👷 Удалить позицию", callback_data=RemoveFilterAction.REMOVE_POSITION + list_type),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить мин. длительность", callback_data=RemoveFilterAction.REMOVE_LONGER + list_type),
                InlineKeyboardButton(text="🗑 Удалить макс. длительность", callback_data=RemoveFilterAction.REMOVE_SHORTER + list_type),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=ModifyFilterAction.MODIFY_MENU + list_type),
            ],
        ]
    )


def add_min_duration_keyboard(list_type: str, durations: list[int]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⏱ {str(duration)}",
                    callback_data=CallbackWithIdAction.ADD_LONGER + list_type + ":" + str(duration)
                ) for duration in durations
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=ModifyFilterAction.MODIFY_MENU + list_type),
            ]
        ]
    )


def add_max_duration_keyboard(list_type: str, durations: list[int]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"⏱ {str(duration)}", callback_data=CallbackWithIdAction.ADD_SHORTER + list_type + ":" + str(duration)) for duration in durations
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=ModifyFilterAction.MODIFY_MENU + list_type),
            ]
        ]
    )


def remove_position_keyboard(list_type: str, positions: list[ListFieldBase]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"❌ {position.value}", callback_data=CallbackWithIdAction.REMOVE_POSITION + list_type + ":" + str(position.id)) for position in positions
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=ModifyFilterAction.MODIFY_MENU + list_type),
            ]
        ]
    )


def remove_company_keyboard(list_type: str, companies: list[ListFieldBase]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"❌ {company.value}", callback_data=CallbackWithIdAction.REMOVE_COMPANY + list_type + ":" + str(company.id)) for company in companies
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=ModifyFilterAction.MODIFY_MENU + list_type),
            ]
        ]
    )


def remove_location_keyboard(list_type: str, locations: list[ListFieldBase]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"❌ {location.value}", callback_data=CallbackWithIdAction.REMOVE_LOCATION + list_type + ":" + str(location.id)) for location in locations
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=ModifyFilterAction.MODIFY_MENU + list_type),
            ]
        ]
    )


def get_back_to_manage_keyboard(list_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к управлению",
                    callback_data=ModifyFilterAction.MODIFY_MENU + list_type
                )
            ]
        ]
    )


def position_selection_keyboard(list_type: str) -> InlineKeyboardMarkup:
    buttons = []
    for position in POSITION_LIST:
        text = f"{position}"
        callback_data = CallbackWithIdAction.SELECT_POSITION + list_type + ":" + position

        buttons.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=ModifyFilterAction.MODIFY_MENU + list_type
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def shift_mute_keyboard(shift_link: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔇 Заглушить",
                    callback_data=CallbackWithIdAction.MUTE_SHIFT + str(shift_link)
                )
            ]
        ]
    )


def set_logic_keyboard(list_type: str, current_is_and: bool = True) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ И (AND)" if current_is_and else "☐ И (AND)",
                    callback_data=CallbackWithIdAction.SET_IS_AND + list_type + ":true"
                ),
                InlineKeyboardButton(
                    text=f"✅ ИЛИ (OR)" if not current_is_and else "☐ ИЛИ (OR)",
                    callback_data=CallbackWithIdAction.SET_IS_AND + list_type + ":false"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=ModifyFilterAction.MODIFY_MENU + list_type
                )
            ]
        ]
    )
    