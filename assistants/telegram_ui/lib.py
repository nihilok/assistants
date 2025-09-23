from functools import wraps
from typing import Protocol, TypeGuard

from telegram import Update, Chat, User
from telegram.ext import ContextTypes
from telegram._message import Message

from assistants.ai.universal import UniversalAssistant  # New unified assistant
from assistants.ai.types import (
    AssistantInterface,
    ThinkingConfig,
)
from assistants.cli.assistant_config import AssistantParams
from assistants.config import environment


class StandardUpdate(Protocol):
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
    return update.effective_chat is not None


def update_has_message(update: Update) -> TypeGuard[Update]:
    return update.message is not None


def requires_effective_chat(func):
    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
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
        assert update.message is not None
        return await func(update, context, *args, **kwargs)
    return wrapped


def requires_reply_to_message(f):
    @requires_effective_chat
    @requires_message
    @wraps(f)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


def build_telegram_specific_instructions():
    instructions = f"""\
{environment.ASSISTANT_INSTRUCTIONS}
N.B. All messages are prefixed with the name of the user who sent them. You should ignore this for the most part, 
and you should not prefix your responses with your own name. You may use the users' names in your responses for clarity
if/when there are multiple users involved.
"""
    return instructions

def build_assistant_params(model_name: str) -> AssistantParams:
    thinking_config = ThinkingConfig.get_thinking_config(
        0, environment.DEFAULT_MAX_RESPONSE_TOKENS
    )

    params = AssistantParams(
        model=model_name,
        max_history_tokens=environment.DEFAULT_MAX_HISTORY_TOKENS,
        max_response_tokens=environment.DEFAULT_MAX_RESPONSE_TOKENS,
        thinking=thinking_config,
        instructions=build_telegram_specific_instructions(),
    )

    params.tools = [{"type": "code_interpreter"}, {"type": "web_search"}]
    return params


def get_telegram_assistant() -> AssistantInterface:
    params = build_assistant_params(environment.DEFAULT_MODEL)
    return UniversalAssistant(**params.to_dict())


assistant = get_telegram_assistant()