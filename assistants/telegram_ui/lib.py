from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes


def requires_reply_to_message(f):
    @wraps(f)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await f(update, context)
        except AttributeError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You must reply to a message from the target user to use this command",
            )

    return wrapper
