from functools import wraps
from typing import Type, Protocol

from telegram import Update, Chat, User
from telegram.ext import ContextTypes
from telegram._message import Message

from assistants.ai.openai import OpenAIAssistant
from assistants.ai.types import (
    AssistantInterface,
    ThinkingConfig,
)
from assistants.cli.assistant_config import AssistantParams
from assistants.cli.utils import get_model_class
from assistants.config import environment

from typing import TypeGuard


# Define Protocol type for Update with non-None properties
class StandardUpdate(Protocol):
    """Protocol for Update with non-None properties."""

    update_id: int

    @property
    def effective_chat(self) -> Chat: ...

    @property
    def message(self) -> Message: ...

    @property
    def effective_message(self) -> Message: ...

    @property
    def effective_user(self) -> "User": ...


def update_has_effective_chat(update: Update) -> TypeGuard[StandardUpdate]:
    """TypeGuard to ensure update.effective_chat is not None."""
    return update.effective_chat is not None


def update_has_message(update: Update) -> TypeGuard[Update]:
    """TypeGuard to ensure update.message is not None."""
    return update.message is not None


def requires_effective_chat(func):
    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # Use assert to convince mypy that update.effective_chat is not None
        if update_has_effective_chat(update):
            return await func(update, context, *args, **kwargs)
        return None

    return wrapped


def requires_message(func):
    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        if not update_has_message(update):
            return None
        # Use assert to convince mypy that update.message is not None
        assert update.message is not None
        return await func(update, context, *args, **kwargs)

    return wrapped


def requires_reply_to_message(f):
    @requires_effective_chat
    @requires_message
    @wraps(f)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # The decorators above ensure that update.effective_chat and update.message are not None
        assert update.effective_chat is not None
        assert update.message is not None

        if update.message.reply_to_message is None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You must reply to a message from the target user to use this command",
            )
            return None

        return await f(update, context)

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
        params.tools = [{"type": "code_interpreter"}, {"type": "web_search"}]

    return params, model_class


def get_telegram_assistant() -> AssistantInterface:
    """
    Get the OpenAI Assistant instance configured for Telegram.
    """
    params, model_class = build_assistant_params(environment.DEFAULT_MODEL)
    return model_class(**params.to_dict())


assistant = get_telegram_assistant()
