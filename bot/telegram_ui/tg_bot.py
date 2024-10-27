import asyncio
import os
from functools import wraps

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)

from bot.telegram_ui.sqlite_user_data import SqliteUserData
from bot.telegram_ui.user_data import NotAuthorized

user_data = SqliteUserData()


def restricted_access(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        try:
            await user_data.check_chat_authorised(update.effective_chat.id)
        except NotAuthorized:
            await user_data.check_user_authorised(update.effective_user.id)

        return await f(update, *args, **kwargs)

    return wrapper


@restricted_access
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)


def build_bot(token: str) -> Application:
    application = ApplicationBuilder().token(token).build()
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    return application


def run_polling(application: Application):
    application.run_polling()


if __name__ == "__main__":
    BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    run_polling(build_bot(BOT_TOKEN))
