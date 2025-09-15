from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import timedelta, datetime

from ..constants.handlers_constants import AdminPanelAction, MainMenuAction
from ..services import MessageService
from ..services.user_service import UserService
from .keyboards.admin_keyboard import admin_panel_keyboard, back_to_admin_panel_keyboard
from ..schemas import UserBase
from ..utils.username_utils import get_username_from_chat_id


class AdminInputStates(StatesGroup):
    waiting_for_username_grant_admin = State()
    waiting_for_username_revoke_admin = State()
    waiting_for_username_activate = State()
    waiting_for_username_deactivate = State()
    waiting_for_activation_time = State()
    waiting_for_message_to_all = State()


admin_router = Router(name="admin")


async def format_user_info(user: UserBase, bot) -> str:
    username = await get_username_from_chat_id(user.tg_id, bot)

    status = f"✅ Активен до {user.access_ends.strftime('%d.%m.%Y %H:%M')}" \
        if user.access_ends and user.access_ends > datetime.utcnow() else "❌ Неактивен"
    admin_status = "👑 Админ" if user.is_admin else "👤 Пользователь"

    return f"""
            👤 {username}
            🆔 ID: {user.tg_id}
            {status}
            {admin_status}
            📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}
            """


def parse_activation_time(time_str: str) -> timedelta:
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            raise ValueError("Неверный формат. Используйте: месяц:день (например: 3:15)")
        
        months = int(parts[0])
        days = int(parts[1])
        
        if months < 0 or days < 0:
            raise ValueError("Время не может быть отрицательным")
        
        total_days = months * 30 + days
        return timedelta(days=total_days)
        
    except ValueError as e:
        raise ValueError(f"Ошибка парсинга времени: {e}")


@admin_router.callback_query(F.data == AdminPanelAction.VIEW_ALL_USERS)
async def on_view_all_users(callback: CallbackQuery) -> None:
    await callback.answer()
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(callback.message.chat.id)):
        await callback.answer("❌ У вас нет прав администратора")
    users = await user_service.get_all_users()
    
    if not users:
        await callback.message.edit_text(
            "Пользователи не найдены",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    message_text = "Все пользователи:\n\n"
    for user in users:
        user_info = await format_user_info(user, callback.bot)
        message_text += user_info + "\n"
    
    if len(message_text) > 4000:
        message_text = message_text[:3900] + "\n\n... (показаны первые пользователи)"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=back_to_admin_panel_keyboard(),
    )


@admin_router.callback_query(F.data == AdminPanelAction.VIEW_ACTIVE_USERS)
async def on_view_active_users(callback: CallbackQuery) -> None:
    await callback.answer()
    
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(callback.message.chat.id)):
        await callback.answer("❌ У вас нет прав администратора")
    users = await user_service.get_active_users()
    
    if not users:
        await callback.message.edit_text(
            "✅ Активные пользователи не найдены",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    message_text = "✅ <b>Активные пользователи:</b>\n\n"
    for user in users:
        user_info = await format_user_info(user, callback.bot)
        message_text += user_info + "\n"
    
    if len(message_text) > 4000:
        message_text = message_text[:3900] + "\n\n... (показаны первые пользователи)"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=back_to_admin_panel_keyboard(),
    )


@admin_router.callback_query(F.data == AdminPanelAction.VIEW_ADMIN_USERS)
async def on_view_admin_users(callback: CallbackQuery) -> None:
    await callback.answer()
    
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(callback.message.chat.id)):
        await callback.answer("❌ У вас нет прав администратора")
    admins = await user_service.get_admins()
    
    if not admins:
        await callback.message.edit_text(
            "👑 Администраторы не найдены",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    message_text = "👑 Администраторы:\n\n"
    for admin in admins:
        admin_info = await format_user_info(admin, callback.bot)
        message_text += admin_info + "\n"
    
    if len(message_text) > 4000:
        message_text = message_text[:3900] + "\n\n... (показаны первые администраторы)"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=back_to_admin_panel_keyboard(),
    )


@admin_router.callback_query(F.data == AdminPanelAction.GRANT_ADMIN)
async def on_grant_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(AdminInputStates.waiting_for_username_grant_admin)
    
    await callback.message.edit_text(
        "➕ <b>Назначение админ прав</b>\n\n"
        "Введите username пользователя (например: @username или username):",
        reply_markup=back_to_admin_panel_keyboard()
    )


@admin_router.message(AdminInputStates.waiting_for_username_grant_admin)
async def handle_grant_admin_username(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    username = message.text.strip()
    
    try:
        await message.delete()
    except:
        pass
    
    if not username:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Имя пользователя не может быть пустым. Попробуйте снова.",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    username = username.lstrip('@')
    
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(message.chat.id)):
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ У вас нет прав администратора",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    try:
        if username.isdigit():
            user = await user_service.get_user_by_tg_id(int(username))
        else:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Поиск только по айди.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        if not user:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Пользователь не найден.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        
        if user.is_admin:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Пользователь уже является администратором.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        
        await user_service.grant_admin(user.id)

        message_service = MessageService.get_instance()
        admin_notification = f"👑 <b>Уведомление администратора</b>\n\n" \
                             f"Пользователю {username} (ID: {user.id}) назначены админские права\n" \
                             f"Администратор: {message.from_user.username or message.from_user.first_name}"
        await message_service.send_message_all_admin(admin_notification, protect_content=False)
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"✅ Админ права назначены пользователю {username}",
            reply_markup=back_to_admin_panel_keyboard()
        )
        
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Неверный формат username. Используйте @username или ID пользователя.",
            reply_markup=back_to_admin_panel_keyboard()
        )
    except Exception as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_keyboard()
        )
    
    await state.clear()


@admin_router.callback_query(F.data == AdminPanelAction.REVOKE_ADMIN)
async def on_revoke_admin_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(AdminInputStates.waiting_for_username_revoke_admin)
    
    await callback.message.edit_text(
        "➖ <b>Отзыв админ прав</b>\n\n"
        "Введите username пользователя (например: @username или username):",
        reply_markup=back_to_admin_panel_keyboard()
    )


@admin_router.message(AdminInputStates.waiting_for_username_revoke_admin)
async def handle_revoke_admin_username(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    username = message.text.strip()
    
    try:
        await message.delete()
    except:
        pass
    
    if not username:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Имя пользователя не может быть пустым. Попробуйте снова.",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    username = username.lstrip('@')
    
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(message.chat.id)):
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ У вас нет прав администратора",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    try:
        if username.isdigit():
            user = await user_service.get_user_by_tg_id(int(username))
        else:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Поиск только по айди.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        if not user:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Пользователь не найден.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        
        if not user.is_admin:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Пользователь не является администратором.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        
        await user_service.revoke_admin(user.id)

        message_service = MessageService.get_instance()
        admin_notification = f"👤 <b>Уведомление администратора</b>\n\n" \
                             f"У пользователя {username} (ID: {user.id}) отозваны админские права\n" \
                             f"Администратор: {message.from_user.username or message.from_user.first_name}"
        await message_service.send_message_all_admin(admin_notification, protect_content=False)
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"✅ Админ права отозваны у пользователя {username}",
            reply_markup=back_to_admin_panel_keyboard()
        )
        
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Неверный формат username. Используйте @username или ID пользователя.",
            reply_markup=back_to_admin_panel_keyboard()
        )
    except Exception as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_keyboard()
        )
    
    await state.clear()


@admin_router.callback_query(F.data == AdminPanelAction.ACTIVATE_USER)
async def on_activate_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(AdminInputStates.waiting_for_username_activate)
    
    await callback.message.edit_text(
        "🔓 <b>Активация пользователя</b>\n\n"
        "Введите username пользователя (например: @username или username):",
        reply_markup=back_to_admin_panel_keyboard()
    )


@admin_router.message(AdminInputStates.waiting_for_username_activate)
async def handle_activate_user_username(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    username = message.text.strip()
    
    try:
        await message.delete()
    except:
        pass
    
    if not username:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Имя пользователя не может быть пустым. Попробуйте снова.",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    username = username.lstrip('@')
    
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(message.chat.id)):
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ У вас нет прав администратора",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    try:
        if username.isdigit():
            user = await user_service.get_user_by_tg_id(int(username))
        else:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Поиск только по айди.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        
        if not user:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Пользователь не найден.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        
        await state.update_data(user_id=user.id, username=username)
        await state.set_state(AdminInputStates.waiting_for_activation_time)
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="⏰ <b>Установка времени доступа</b>\n\n"
                 "Введите время в формате 'месяц:день' (например: 3:15 для 3 месяцев и 15 дней):",
            reply_markup=back_to_admin_panel_keyboard()
        )
        
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Неверный формат username. Используйте @username или ID пользователя.",
            reply_markup=back_to_admin_panel_keyboard()
        )
    except Exception as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_keyboard()
        )


@admin_router.message(AdminInputStates.waiting_for_activation_time)
async def handle_activation_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    time_str = message.text.strip()
    
    try:
        await message.delete()
    except:
        pass
    
    if not time_str:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="Время не может быть пустым. Попробуйте снова.",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    try:
        time_delta = parse_activation_time(time_str)
        user_id = data.get('user_id')
        username = data.get('username')
        
        if not user_id:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Ошибка: данные пользователя не найдены.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            await state.clear()
            return
        
        user_service = UserService.get_instance()
        await user_service.activate(user_id, time_delta)
        
        message_service = MessageService.get_instance()
        admin_notification = f"🔓 <b>Уведомление администратора</b>\n\n" \
                             f"Пользователь {username} (ID: {user_id}) был активирован на {time_str}\n" \
                             f"Администратор: {message.from_user.username or message.from_user.first_name}"
        await message_service.send_message_all_admin(admin_notification, protect_content=False)
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"✅ Пользователь {username} активирован на {time_str}",
            reply_markup=back_to_admin_panel_keyboard()
        )
        
    except ValueError as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"❌ {str(e)}",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    except Exception as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_keyboard()
        )
    
    await state.clear()


@admin_router.callback_query(F.data == AdminPanelAction.DEACTIVATE_USER)
async def on_deactivate_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(AdminInputStates.waiting_for_username_deactivate)
    
    await callback.message.edit_text(
        "🔒 <b>Деактивация пользователя</b>\n\n"
        "Введите username пользователя (например: @username или username):",
        reply_markup=back_to_admin_panel_keyboard()
    )


@admin_router.message(AdminInputStates.waiting_for_username_deactivate)
async def handle_deactivate_user_username(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    username = message.text.strip()
    
    try:
        await message.delete()
    except:
        pass
    
    if not username:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Имя пользователя не может быть пустым. Попробуйте снова.",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    username = username.lstrip('@')
    
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(message.chat.id)):
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ У вас нет прав администратора",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    try:
        if username.isdigit():
            user = await user_service.get_user_by_tg_id(int(username))
        else:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Поиск только по айди.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return
        
        if not user:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=bot_message_id,
                text="❌ Пользователь не найден.",
                reply_markup=back_to_admin_panel_keyboard()
            )
            return

        await user_service.deactivate(user.id)

        message_service = MessageService.get_instance()
        admin_notification = f"🔒 <b>Уведомление администратора</b>\n\n" \
                             f"Пользователь {username} (ID: {user.id}) был деактивирован\n" \
                             f"Администратор: {message.from_user.username or message.from_user.first_name}"
        await message_service.send_message_all_admin(admin_notification, protect_content=False)
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"✅ Пользователь {username} деактивирован",
            reply_markup=back_to_admin_panel_keyboard()
        )
        
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Неверный формат username. Используйте @username или ID пользователя.",
            reply_markup=back_to_admin_panel_keyboard()
        )
    except Exception as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=back_to_admin_panel_keyboard()
        )
    
    await state.clear()


@admin_router.callback_query(F.data == AdminPanelAction.BACK_TO_ADMIN_PANEL)
async def on_back_to_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_keyboard()
    )


@admin_router.callback_query(F.data == AdminPanelAction.SEND_MESSAGE_TO_ALL)
async def on_send_message_to_all_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(AdminInputStates.waiting_for_message_to_all)
    
    await callback.message.edit_text(
        "📢 <b>Отправка сообщения всем пользователям</b>\n\n"
        "Введите сообщение, которое будет отправлено всем пользователям:",
        reply_markup=back_to_admin_panel_keyboard()
    )


@admin_router.message(AdminInputStates.waiting_for_message_to_all)
async def handle_message_to_all(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    message_text = message.text.strip()
    
    try:
        await message.delete()
    except:
        pass
    
    if not message_text:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ Сообщение не может быть пустым. Попробуйте снова.",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    user_service = UserService.get_instance()
    if not user_service.check_admin(await user_service.get_user_by_tg_id(message.chat.id)):
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="❌ У вас нет прав администратора.",
            reply_markup=back_to_admin_panel_keyboard()
        )
        return
    
    try:
        message_service = MessageService.get_instance()
        
        await message_service.send_message_all_users(message_text, protect_content=False)
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"✅ Сообщение отправлено всем пользователям:\n\n{message_text}",
            reply_markup=back_to_admin_panel_keyboard()
        )
        
    except Exception as e:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text=f"❌ Ошибка при отправке сообщения: {str(e)}",
            reply_markup=back_to_admin_panel_keyboard()
        )
    
    await state.clear()


@admin_router.callback_query(F.data == MainMenuAction.ADMIN_PANEL)
async def on_back_to_admin_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_keyboard()
    )


