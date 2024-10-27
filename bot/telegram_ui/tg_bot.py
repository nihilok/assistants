import os
from functools import wraps

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)

from bot.ai.assistant import Assistant
from bot.telegram_ui.sqlite_user_data import SqliteUserData
from bot.telegram_ui.user_data import NotAuthorized, ChatHistory

user_data = SqliteUserData()

assistant = Assistant(
    name=os.getenv("ASSISTANT_NAME"),
    model=os.getenv("ASSISTANT_MODEL"),
    instructions=os.getenv("ASSISTANT_INSTRUCTIONS"),
    tools=[{"type": "code_interpreter"}],
    api_key=os.getenv("ASSISTANT_API_KEY"),
)


def restricted_access(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        try:
            await user_data.check_chat_authorised(update.effective_chat.id)
        except NotAuthorized:
            await user_data.check_user_authorised(update.effective_user.id)

        return await f(update, *args, **kwargs)

    return wrapper


def requires_superuser(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        await user_data.check_superuser(update.effective_user.id)

        return await f(update, *args, **kwargs)

    return wrapper


@requires_superuser
async def promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await user_data.promote_superuser(update.message.reply_to_message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="User promoted"
    )


@requires_superuser
async def demote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await user_data.demote_superuser(update.message.reply_to_message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="User demoted"
    )


@requires_superuser
async def authorise_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await user_data.authorise_chat(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Chat authorised"
    )


@requires_superuser
async def authorise_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await user_data.authorise_chat(update.message.reply_to_message.from_user.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="User authorised"
        )
    except AttributeError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You must reply to a message from the target user to use this command",
        )


@requires_superuser
async def deauthorise_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await user_data.deauthorise_chat(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Chat de-authorised"
    )


@requires_superuser
async def deauthorise_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await user_data.deauthorise_user(update.message.reply_to_message.from_user.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="User de-authorised"
        )
    except AttributeError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You must reply to a message from the target user to use this command",
        )


@restricted_access
async def new_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await user_data.clear_last_thread_id(update.effective_chat.id)


@restricted_access
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    existing_chat = await user_data.get_chat_history(update.effective_chat.id)
    response_message = await assistant.converse(
        update.message.text, existing_chat.thread_id
    )
    if not existing_chat.thread_id:
        await user_data.save_chat_history(
            ChatHistory(
                chat_id=update.effective_chat.id, thread_id=response_message.thread_id
            )
        )

    response = response_message.content[0].text.value

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


def build_bot(token: str) -> Application:
    application = ApplicationBuilder().token(token).build()
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    application.add_handler(CommandHandler("auth_chat", authorise_chat))
    application.add_handler(CommandHandler("deauth_chat", deauthorise_chat))
    application.add_handler(CommandHandler("auth_user", authorise_user))
    application.add_handler(CommandHandler("deauth_user", deauthorise_user))
    application.add_handler(CommandHandler("promote", promote_user))
    application.add_handler(CommandHandler("demote", demote_user))
    application.add_handler(CommandHandler("new_thread", new_thread))
    return application


def run_polling(application: Application):
    application.run_polling()


if __name__ == "__main__":
    BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    run_polling(build_bot(BOT_TOKEN))
