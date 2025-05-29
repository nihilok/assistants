from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from assistants.ai.openai import OpenAIAssistant, OpenAICompletion
from assistants.config import environment


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


assistant = OpenAIAssistant(
    model=environment.DEFAULT_MODEL,
    instructions=environment.ASSISTANT_INSTRUCTIONS,
    tools=[{"type": "code_interpreter"}],
    api_key=environment.OPENAI_API_KEY,
)

audio_completion = OpenAICompletion(
    model="gpt-4o-audio-preview",
    api_key=environment.OPENAI_API_KEY,
)
