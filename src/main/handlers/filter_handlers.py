from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import timedelta

from ..constants.handlers_constants import (
    FilterAction,
    ModifyFilterAction,
    AddFilterAction,
    RemoveFilterAction,
    CallbackWithIdAction, DURATION_LIST, MainMenuAction,
)
from ..services.user_service import UserService
from .keyboards import (
    filters_menu_keyboard,
    filter_manage_keyboard,
    add_rule_menu_keyboard,
    remove_rule_menu_keyboard,
    add_min_duration_keyboard,
    add_max_duration_keyboard,
    get_back_to_manage_keyboard, remove_position_keyboard, remove_location_keyboard, remove_company_keyboard,
    position_selection_keyboard,
    set_logic_keyboard,
)
from ..schemas import FilterBase

filter_router = Router(name="filter")


class FilterInputStates(StatesGroup):
    add_company = State()
    add_location = State()
    add_position = State()


@filter_router.callback_query(F.data == MainMenuAction.FILTERS)
async def on_filters_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("Выберите список для управления:", reply_markup=filters_menu_keyboard())


@filter_router.callback_query(F.data == FilterAction.FILTERS_MENU)
async def back_on_filters_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("Выберите список для управления:", reply_markup=filters_menu_keyboard())


@filter_router.callback_query(F.data == FilterAction.WHITE_LIST)
async def on_white_list(callback: CallbackQuery) -> None:
    await callback.answer()

    # Получаем фильтр пользователя
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text("Пользователь не найден", reply_markup=filter_manage_keyboard("wl"))
        return

    filters = await user_service.get_user_filters(user.id)
    white_filter = next((f for f in filters if not f.is_black_list), None)

    # Формируем сообщение с информацией о фильтре
    message_text = "Белый список:"
    if white_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(white_filter)
        message_text += f"\n\n{filter_info}"
    else:
        message_text += "\n\n📝 Фильтр не настроен"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard("wl"))


@filter_router.callback_query(F.data == FilterAction.BLACK_LIST)
async def on_black_list(callback: CallbackQuery) -> None:
    await callback.answer()

    # Получаем фильтр пользователя
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text("Пользователь не найден", reply_markup=filter_manage_keyboard("bl"))
        return

    filters = await user_service.get_user_filters(user.id)
    black_filter = next((f for f in filters if f.is_black_list), None)

    # Формируем сообщение с информацией о фильтре
    message_text = "Чёрный список:"
    if black_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(black_filter)
        message_text += f"\n\n{filter_info}"
    else:
        message_text += "\n\n📝 Фильтр не настроен"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard("bl"))


@filter_router.callback_query(F.data.startswith(ModifyFilterAction.ADD_RULE))
async def on_add_rule_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(ModifyFilterAction.ADD_RULE)
    await callback.message.edit_text("Выберите, что добавить:", reply_markup=add_rule_menu_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(ModifyFilterAction.DELETE_RULE))
async def on_delete_rule_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(ModifyFilterAction.DELETE_RULE)
    await callback.message.edit_text("Выберите, что удалить:", reply_markup=remove_rule_menu_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(ModifyFilterAction.MODIFY_MENU))
async def on_back_to_modify_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(ModifyFilterAction.MODIFY_MENU)
    await state.clear()
    await callback.message.edit_text(
        "Меню управления:", reply_markup=filter_manage_keyboard(list_type)
    )


@filter_router.callback_query(F.data.startswith(ModifyFilterAction.SET_LOGIC))
async def on_set_logic_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(ModifyFilterAction.SET_LOGIC)

    # Get current filter to show current logic setting
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text("Пользователь не найден.")
        return

    # Get user's filter for this list type
    is_black_list = list_type == "bl"
    filters = await user_service.get_user_filters(user.id)
    current_filter = None

    for filter_obj in filters:
        if filter_obj.is_black_list == is_black_list:
            current_filter = filter_obj
            break

    current_is_and = current_filter.is_and if current_filter and current_filter.is_and is not None else True

    await callback.message.edit_text(
        f"Выберите логику для {'чёрного' if is_black_list else 'белого'} списка:",
        reply_markup=set_logic_keyboard(list_type, current_is_and)
    )


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.SET_IS_AND))
async def on_set_is_and(callback: CallbackQuery) -> None:
    await callback.answer()
    callback_data = callback.data.removeprefix(CallbackWithIdAction.SET_IS_AND)
    list_type, is_and_str = callback_data.split(":")
    is_and = is_and_str.lower() == "true"

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)

    if not user:
        await callback.message.edit_text("Пользователь не найден.")
        return

    is_black_list = list_type == "bl"
    filters = await user_service.get_user_filters(user.id)

    for filter_obj in filters:
        if filter_obj.is_black_list == is_black_list:
            update_filter = FilterBase(
                id=filter_obj.id,
                is_and=is_and
            )
            await user_service.update_filter(update_filter)

    logic_text = "И (AND)" if is_and else "ИЛИ (OR)"
    list_text = "чёрного" if is_black_list else "белого"

    await callback.message.edit_text(
        f"✅ Логика {list_text} списка установлена: {logic_text}",
        reply_markup=set_logic_keyboard(list_type, is_and)
    )


@filter_router.callback_query(F.data.startswith(AddFilterAction.ADD_COMPANY))
async def on_add_company(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(AddFilterAction.ADD_COMPANY)
    await state.update_data(list_type=list_type, bot_message_id=callback.message.message_id)
    await state.set_state(FilterInputStates.add_company)
    await callback.message.edit_text(
        f"Отправьте название компании для добавления в {'белый' if list_type == 'wl' else 'чёрный'} список.",
        reply_markup=get_back_to_manage_keyboard(list_type)
    )


@filter_router.message(FilterInputStates.add_company, F.text)
async def handle_add_company(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    list_type = data.get("list_type")
    bot_message_id = data.get("bot_message_id")
    company_name = message.text.strip()

    try:
        await message.delete()
    except:
        pass

    if not company_name:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Название компании не может быть пустым. Попробуйте снова.",
            reply_markup=get_back_to_manage_keyboard(list_type)
        )
        return

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Пользователь не найден",
            reply_markup=filter_manage_keyboard(list_type)
        )
        return

    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Фильтр не найден",
            reply_markup=filter_manage_keyboard(list_type)
        )
        return

    await user_service.add_filter_company(my_filter.id, company_name)
    await state.clear()

    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "✅ Компания добавлена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=bot_message_id,
        text=message_text,
        reply_markup=filter_manage_keyboard(list_type)
    )


@filter_router.callback_query(F.data.startswith(AddFilterAction.ADD_LOCATION))
async def on_add_location(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(AddFilterAction.ADD_LOCATION)
    await state.update_data(list_type=list_type, bot_message_id=callback.message.message_id)
    await state.set_state(FilterInputStates.add_location)
    await callback.message.edit_text(
        f"Отправьте название локации для добавления в {'белый' if list_type == 'wl' else 'чёрный'} список.",
        reply_markup=get_back_to_manage_keyboard(list_type)
    )


@filter_router.message(FilterInputStates.add_location, F.text)
async def handle_add_location(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    list_type = data.get("list_type")
    bot_message_id = data.get("bot_message_id")
    location_name = message.text.strip()

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass  # Игнорируем ошибки удаления

    if not location_name:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Название локации не может быть пустым. Попробуйте снова.",
            reply_markup=get_back_to_manage_keyboard(list_type)
        )
        return

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Пользователь не найден",
            reply_markup=filter_manage_keyboard(list_type)
        )
        return

    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Фильтр не найден",
            reply_markup=filter_manage_keyboard(list_type)
        )
        return

    await user_service.add_filter_location(my_filter.id, location_name)
    await state.clear()

    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "✅ Локация добавлена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=bot_message_id,
        text=message_text,
        reply_markup=filter_manage_keyboard(list_type)
    )


@filter_router.callback_query(F.data.startswith(AddFilterAction.ADD_POSITION))
async def on_add_position(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(AddFilterAction.ADD_POSITION)
    await callback.message.edit_text(
        f"Выберите позиции для добавления в {'белый' if list_type == 'wl' else 'чёрный'} список:",
        reply_markup=position_selection_keyboard(list_type)
    )


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.SELECT_POSITION))
async def on_select_position(callback: CallbackQuery) -> None:
    await callback.answer()
    tail = callback.data.removeprefix(CallbackWithIdAction.SELECT_POSITION)
    list_type, position = tail.split(":", 1)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return

    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    existing_positions = [p.value for p in my_filter.positions]
    if position not in existing_positions:
        await user_service.add_filter_position(my_filter.id, position)

        updated_filters = await user_service.get_user_filters(user.id)
        updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

        message_text = "✅ Позиция добавлена"
        if updated_filter:
            from ..services.shift_service import ShiftService
            filter_info = ShiftService.format_filter_for_telegram(updated_filter)
            message_text += f"\n\n{filter_info}"

        await callback.message.edit_text(
            text=message_text,
            reply_markup=filter_manage_keyboard(list_type)
        )
    else:
        await callback.message.edit_text(
            f"Выберите позиции для добавления в {'белый' if list_type == 'wl' else 'чёрный'} список:",
            reply_markup=position_selection_keyboard(list_type)
        )


@filter_router.callback_query(F.data.startswith(AddFilterAction.ADD_LONGER))
async def on_add_longer_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(AddFilterAction.ADD_LONGER)
    await callback.message.edit_text(
        "Выберите минимальную длительность:",
        reply_markup=add_min_duration_keyboard(list_type, DURATION_LIST),
    )


@filter_router.callback_query(F.data.startswith(AddFilterAction.ADD_SHORTER))
async def on_add_shorter_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(AddFilterAction.ADD_SHORTER)
    await callback.message.edit_text(
        "Выберите максимальную длительность:",
        reply_markup=add_max_duration_keyboard(list_type, DURATION_LIST),
    )


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.ADD_LONGER))
async def on_set_longer(callback: CallbackQuery) -> None:
    await callback.answer()
    tail = callback.data.removeprefix(CallbackWithIdAction.ADD_LONGER)
    list_type, hours_str = tail.split(":", 1)
    hours = int(hours_str)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    await user_service.update_filter(FilterBase(id=my_filter.id, longer=timedelta(hours=hours)))

    # Получаем обновленный фильтр и показываем его состояние
    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "✅ Минимальная длительность обновлена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.ADD_SHORTER))
async def on_set_shorter(callback: CallbackQuery) -> None:
    await callback.answer()
    tail = callback.data.removeprefix(CallbackWithIdAction.ADD_SHORTER)
    list_type, hours_str = tail.split(":", 1)
    hours = int(hours_str)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    await user_service.update_filter(FilterBase(id=my_filter.id, shorter=timedelta(hours=hours)))

    # Получаем обновленный фильтр и показываем его состояние
    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "✅ Максимальная длительность обновлена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(RemoveFilterAction.REMOVE_COMPANY))
async def on_remove_company_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(RemoveFilterAction.REMOVE_COMPANY)
    tg_id = callback.message.chat.id
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(tg_id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return
    await callback.message.edit_text(
        f"Выберите название компании для удаления из {'белого' if list_type == 'wl' else 'чёрного'} списка.",
        reply_markup=remove_company_keyboard(list_type, my_filter.companies),
    )


@filter_router.callback_query(F.data.startswith(RemoveFilterAction.REMOVE_LOCATION))
async def on_remove_location_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(RemoveFilterAction.REMOVE_LOCATION)
    tg_id = callback.message.chat.id
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(tg_id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return
    await callback.message.edit_text(
        f"Выберите название локации для удаления из {'белого' if list_type == 'wl' else 'чёрного'} списка.",
        reply_markup=remove_location_keyboard(list_type, my_filter.locations),
    )


@filter_router.callback_query(F.data.startswith(RemoveFilterAction.REMOVE_POSITION))
async def on_remove_position_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(RemoveFilterAction.REMOVE_POSITION)
    tg_id = callback.message.chat.id
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(tg_id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return
    await callback.message.edit_text(
        f"Выберите название позиции для удаления из {'белого' if list_type == 'wl' else 'чёрного'} списка.",
        reply_markup=remove_position_keyboard(list_type, my_filter.positions),
    )


@filter_router.callback_query(F.data.startswith(RemoveFilterAction.REMOVE_LONGER))
async def on_remove_longer(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(RemoveFilterAction.REMOVE_LONGER)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    await user_service.clear_filter_longer(my_filter.id)

    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "🗑 Минимальная длительность удалена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(RemoveFilterAction.REMOVE_SHORTER))
async def on_remove_shorter(callback: CallbackQuery) -> None:
    await callback.answer()
    list_type = callback.data.removeprefix(RemoveFilterAction.REMOVE_SHORTER)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    await user_service.clear_filter_shorter(my_filter.id)

    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "🗑 Максимальная длительность удалена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.REMOVE_COMPANY))
async def on_remove_company_by_id(callback: CallbackQuery) -> None:
    await callback.answer()
    tail = callback.data.removeprefix(CallbackWithIdAction.REMOVE_COMPANY)
    list_type, company_id_str = tail.split(":", 1)
    company_id = int(company_id_str)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    await user_service.remove_filter_company(my_filter.id, company_id)

    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "✅ Компания удалена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.REMOVE_LOCATION))
async def on_remove_location_by_id(callback: CallbackQuery) -> None:
    await callback.answer()
    tail = callback.data.removeprefix(CallbackWithIdAction.REMOVE_LOCATION)
    list_type, location_id_str = tail.split(":", 1)
    location_id = int(location_id_str)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    await user_service.remove_filter_location(my_filter.id, location_id)

    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "✅ Локация удалена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.REMOVE_POSITION))
async def on_remove_position_by_id(callback: CallbackQuery) -> None:
    await callback.answer()
    tail = callback.data.removeprefix(CallbackWithIdAction.REMOVE_POSITION)
    list_type, position_id_str = tail.split(":", 1)
    position_id = int(position_id_str)

    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Пользователь не найден")
        return
    filters = await user_service.get_user_filters(user.id)
    is_black = (list_type == "bl")
    my_filter = next((f for f in filters if bool(f.is_black_list) == is_black), None)
    if not my_filter:
        await callback.message.answer("Фильтр не найден")
        return

    await user_service.remove_filter_position(my_filter.id, position_id)

    updated_filters = await user_service.get_user_filters(user.id)
    updated_filter = next((f for f in updated_filters if bool(f.is_black_list) == is_black), None)

    message_text = "✅ Позиция удалена"
    if updated_filter:
        from ..services.shift_service import ShiftService
        filter_info = ShiftService.format_filter_for_telegram(updated_filter)
        message_text += f"\n\n{filter_info}"

    await callback.message.edit_text(message_text, reply_markup=filter_manage_keyboard(list_type))


@filter_router.callback_query(F.data.startswith(CallbackWithIdAction.MUTE_SHIFT))
async def on_mute_shift(callback: CallbackQuery) -> None:
    await callback.answer()
    
    shift_link = int(callback.data.removeprefix(CallbackWithIdAction.MUTE_SHIFT))
    
    user_service = UserService.get_instance()
    user = await user_service.get_user_by_tg_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text("Пользователь не найден.")
        return
    
    from src.main.services.mute_service import MuteService
    mute_service = MuteService.get_instance()
    await mute_service.mute_shift(user.id, shift_link)
    await callback.message.edit_text(
        callback.message.text
    )
