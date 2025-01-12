import os
from functools import wraps

import aiohttp
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from assistants.ai.openai import Assistant
from assistants.config import environment
from assistants.log import logger
from assistants.user_data import threads_table
from assistants.user_data.interfaces.telegram_chat_data import (
    ChatHistory,
    NotAuthorized,
)
from assistants.user_data.sqlite_backend.telegram_chat_data import (
    TelegramSqliteUserData,
)

chat_data = TelegramSqliteUserData()

assistant = Assistant(
    name=environment.ASSISTANT_NAME,
    model=environment.DEFAULT_MODEL,
    instructions=environment.ASSISTANT_INSTRUCTIONS,
    tools=[{"type": "code_interpreter"}],
    api_key=environment.OPENAI_API_KEY,
)


def restricted_access(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        try:
            await chat_data.check_chat_authorised(update.effective_chat.id)
        except NotAuthorized:
            await chat_data.check_user_authorised(update.effective_user.id)

        return await f(update, *args, **kwargs)

    return wrapper


def requires_superuser(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        await chat_data.check_superuser(update.effective_user.id)

        return await f(update, *args, **kwargs)

    return wrapper


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


@requires_superuser
@requires_reply_to_message
async def promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat_data.promote_superuser(update.message.reply_to_message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="User promoted"
    )


@requires_superuser
@requires_reply_to_message
async def demote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat_data.demote_superuser(update.message.reply_to_message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="User demoted"
    )


@requires_superuser
async def authorise_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat_data.authorise_chat(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Chat authorised"
    )


@requires_superuser
@requires_reply_to_message
async def authorise_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat_data.authorise_chat(update.message.reply_to_message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="User authorised"
    )


@requires_superuser
async def deauthorise_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat_data.deauthorise_chat(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Chat de-authorised"
    )


@requires_superuser
@requires_reply_to_message
async def deauthorise_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat_data.deauthorise_user(update.message.reply_to_message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="User de-authorised"
    )


@restricted_access
async def new_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await chat_data.clear_last_thread_id(update.effective_chat.id)
    assistant.last_message = None
    await context.bot.send_message(
        update.effective_chat.id, "Conversation history cleared."
    )


@restricted_access
async def toggle_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_history = await chat_data.get_chat_history(update.effective_chat.id)
    result = "OFF" if chat_history.auto_reply else "ON"
    await chat_data.set_auto_reply(
        update.effective_chat.id, not chat_history.auto_reply
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Auto reply is {result}"
    )


@restricted_access
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    existing_chat = await chat_data.get_chat_history(update.effective_chat.id)
    message_text = update.message.text
    if not existing_chat.auto_reply:
        bot_id = context.bot.id
        bot_username = f"@{context.bot.username}"
        if bot_username not in message_text and (
            not update.message.reply_to_message
            or update.message.reply_to_message.from_user.id != bot_id
        ):
            return
        message_text = message_text.replace(
            bot_username, os.getenv("ASSISTANT_NAME", "[ASSISTANT NAME]")
        )

    response_message = await assistant.converse(message_text, existing_chat.thread_id)

    if not existing_chat.thread_id:
        await chat_data.save_chat_history(
            ChatHistory(
                chat_id=update.effective_chat.id,
                thread_id=response_message.thread_id,
                auto_reply=existing_chat.auto_reply,
            )
        )
        await threads_table.save_thread(
            response_message.thread_id, assistant.assistant_id, message_text
        )

    response = response_message.text_content

    response_parts = response.split("```")

    if len(response_parts) % 2 == 0:
        # Should be an odd number of parts if codeblocks
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
        )
        return

    for i, part in enumerate(response_parts):
        if i % 2:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"```{part}```",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=part,
            )


@restricted_access
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.replace("/image ", "")
    image_url = await assistant.image_prompt(prompt)

    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            image_content = await response.read()

    await update.message.reply_photo(image_content)


def build_bot(token: str) -> Application:
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("add_chat", authorise_chat))
    application.add_handler(CommandHandler("remove_chat", deauthorise_chat))
    application.add_handler(CommandHandler("add_user", authorise_user))
    application.add_handler(CommandHandler("remove_user", deauthorise_user))
    application.add_handler(CommandHandler("promote", promote_user))
    application.add_handler(CommandHandler("demote", demote_user))
    application.add_handler(CommandHandler("new_thread", new_thread))
    application.add_handler(CommandHandler("auto_reply", toggle_auto_reply))
    application.add_handler(CommandHandler("image", generate_image))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    logger.info("Setup complete!")
    return application


def run_polling(application: Application):
    logger.info("Telegram bot is running...")
    application.run_polling()


async def async_setup():
    await assistant.start()


def setup_and_run(token: str):
    application = build_bot(token)
    run_polling(application)
