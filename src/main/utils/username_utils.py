async def get_username_from_chat_id(chat_id: int, bot) -> str:
    try:
        user_info = await bot.get_chat(chat_id)
        if user_info.username:
            return f"@{user_info.username}"
        elif user_info.first_name or user_info.last_name:
            name_parts = []
            if user_info.first_name:
                name_parts.append(user_info.first_name)
            if user_info.last_name:
                name_parts.append(user_info.last_name)
            return " ".join(name_parts)
        else:
            return f"ID: {chat_id}"
    except Exception:
        return f"ID: {chat_id}"

