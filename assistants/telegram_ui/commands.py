import aiohttp
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from assistants.ai.types import MessageDict
from assistants.telegram_ui.auth import (
    chat_data,
    requires_superuser,
    restricted_access,
)
from assistants.telegram_ui.lib import (
    assistant,
    requires_reply_to_message,
)
from assistants.user_data.interfaces.telegram_chat_data import ChatData
from assistants.user_data.sqlite_backend.conversations import get_conversations_table


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
    await get_conversations_table().delete(id=update.effective_chat.id)
    assistant.last_message = None
    await context.bot.send_message(
        update.effective_chat.id, "Conversation history cleared."
    )


@restricted_access
async def toggle_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_data = await chat_data.get_chat_data(update.effective_chat.id)
    result = "OFF" if chat_data.auto_reply else "ON"
    await chat_data.set_auto_reply(update.effective_chat.id, not chat_data.auto_reply)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Auto reply is {result}"
    )


@restricted_access
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    existing_chat = await chat_data.get_chat_data(update.effective_chat.id)
    chat_thread_id = existing_chat.thread_id or update.effective_chat.id
    message_text = update.message.text
    bot_username = f"@{context.bot.username}"
    bot_name = context.bot.first_name or context.bot.username
    bot_tagged = bot_username in message_text
    if bot_tagged:
        message_text = message_text.replace(bot_username, bot_name)

    message_text = f"{update.message.from_user.first_name}: {message_text}"

    if not existing_chat.auto_reply:
        bot_id = context.bot.id
        if not bot_tagged and (
            not update.message.reply_to_message
            or update.message.reply_to_message.from_user.id != bot_id
        ):
            await assistant.remember(
                MessageDict(
                    role="user",
                    content=message_text,
                )
            )
            await assistant.save_conversation_state()
            return

    await assistant.load_conversation(chat_thread_id)

    assistant.instructions = f"""\
{assistant.instructions}
Your Telegram username is '{bot_username}' and your bot's name is '{bot_name}'.
"""

    response_message = await assistant.converse(message_text, existing_chat.thread_id)

    if not existing_chat.thread_id:
        await chat_data.save_chat_data(
            ChatData(
                chat_id=update.effective_chat.id,
                thread_id=str(assistant.conversation_id),
                auto_reply=existing_chat.auto_reply,
            )
        )

    await assistant.save_conversation_state()

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


@restricted_access
async def respond_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    existing_chat = await chat_data.get_chat_data(update.effective_chat.id)

    thread_id = existing_chat.thread_id or str(update.effective_chat.id)

    bot_username = f"@{context.bot.username}"
    bot_name = context.bot.first_name or context.bot.username

    assistant.instructions = f"""\
{assistant.instructions}
Your Telegram username is '{bot_username}' and your bot's name is '{bot_name}'.
"""

    response = await assistant.audio_response(
        update.message.text.replace("/voice ", ""), thread_id=thread_id
    )

    if not existing_chat.thread_id:
        await chat_data.save_chat_data(
            ChatData(
                chat_id=update.effective_chat.id,
                thread_id=str(assistant.conversation_id),
                auto_reply=existing_chat.auto_reply,
            )
        )

    await assistant.save_conversation_state()
    if isinstance(response, bytes):
        await context.bot.send_voice(
            chat_id=update.effective_chat.id,
            voice=response,
            caption="Response",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
        )
