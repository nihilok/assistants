from functools import wraps
from typing import Type

from telegram import Update
from telegram.ext import ContextTypes

from assistants.ai.openai import OpenAIAssistant, OpenAICompletion
from assistants.ai.types import AssistantInterface, ThinkingConfig
from assistants.cli.assistant_config import AssistantParams
from assistants.cli.utils import get_model_class
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
            return None

    return wrapper


def build_assistant_params(
    model_name: str,
) -> tuple[AssistantParams, Type[AssistantInterface]]:
    model_class = get_model_class(model_name, "default")
    if not model_class:
        raise ValueError(f"Model '{model_name}' is not supported for Telegram UI.")

    thinking_config = ThinkingConfig.get_thinking_config(
        0, environment.DEFAULT_MAX_RESPONSE_TOKENS
    )

    # Create the assistant parameters
    params = AssistantParams(
        model=model_name,
        max_history_tokens=environment.DEFAULT_MAX_HISTORY_TOKENS,
        max_response_tokens=environment.DEFAULT_MAX_RESPONSE_TOKENS,
        thinking=thinking_config,
        instructions=environment.ASSISTANT_INSTRUCTIONS,
    )

    # Add tools for OpenAI assistant in non-code mode
    if model_class == OpenAIAssistant:
        params.tools = [{"type": "code_interpreter"}]

    return params, model_class


def get_telegram_assistant() -> AssistantInterface:
    """
    Get the OpenAI Assistant instance configured for Telegram.
    """
    params, model_class = build_assistant_params(environment.DEFAULT_MODEL)
    return model_class(**params.to_dict())


assistant = get_telegram_assistant()

audio_completion = OpenAICompletion(
    model="gpt-4o-audio-preview",
    api_key=environment.OPENAI_API_KEY,
)
