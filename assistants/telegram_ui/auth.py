from functools import wraps

from telegram import Update

from assistants.user_data.interfaces.telegram_chat_data import NotAuthorised
from assistants.user_data.sqlite_backend.telegram_chat_data import (
    TelegramSqliteUserData,
)

chat_data = TelegramSqliteUserData()


def restricted_access(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        try:
            await chat_data.check_chat_authorised(update.effective_chat.id)
        except NotAuthorised:
            await chat_data.check_user_authorised(update.effective_user.id)

        return await f(update, *args, **kwargs)

    return wrapper


def requires_superuser(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        await chat_data.check_superuser(update.effective_user.id)

        return await f(update, *args, **kwargs)

    return wrapper
