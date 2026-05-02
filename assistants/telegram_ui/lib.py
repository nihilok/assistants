from functools import wraps
from typing import Protocol, TypeGuard

from telegram import Update, Chat, User
from telegram.ext import ContextTypes
from telegram._message import Message

from assistants.ai.universal import UniversalAssistant
from assistants.ai.types import (
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


def build_telegram_specific_instructions(
    bot_username: str = "", bot_name: str = ""
) -> str:
    instructions = f"""\
{environment.ASSISTANT_INSTRUCTIONS}
N.B. All messages are prefixed with the Telegram first name of the user who sent them (e.g. "Alice: hello"). \
This prefix is their account name, not a nickname they chose for you. Do not treat it as a name for yourself. \
Do not prefix your own responses with your name. You may address users by their name for clarity \
when there are multiple participants in the conversation.
When the conversation history contains a message like "[Generated image: <prompt>]", it means an image was \
successfully generated from that prompt and already sent to the chat as a photo. You do not need to regenerate \
or describe it — you can refer to it naturally (e.g. "the image of <prompt> I just sent").
"""
    if bot_username and bot_name:
        instructions += f"\nYour Telegram username is '{bot_username}' and your bot's name is '{bot_name}'."
    return instructions


def build_assistant_params(
    model_name: str, bot_username: str = "", bot_name: str = ""
) -> AssistantParams:
    thinking_config = ThinkingConfig.get_thinking_config(
        0, environment.DEFAULT_MAX_RESPONSE_TOKENS
    )

    params = AssistantParams(
        model=model_name,
        max_history_tokens=environment.DEFAULT_MAX_HISTORY_TOKENS,
        max_response_tokens=environment.DEFAULT_MAX_RESPONSE_TOKENS,
        thinking=thinking_config,
        instructions=build_telegram_specific_instructions(bot_username, bot_name),
    )

    # TODO: UniversalAssistant ignores the `tools` kwarg (uses MCP via enable_mcp_tools instead).
    # These OpenAI Assistants-style tool types are leftover from the previous implementation.
    # Either wire up equivalent capabilities via MCP servers or remove this.
    params.tools = [{"type": "code_interpreter"}, {"type": "web_search"}]
    return params


def get_telegram_assistant(
    bot_username: str = "", bot_name: str = ""
) -> UniversalAssistant:
    params = build_assistant_params(environment.DEFAULT_MODEL, bot_username, bot_name)
    return UniversalAssistant(**params.to_dict())


class AssistantRegistry:
    """Per-chat assistant instances, keyed by chat_id."""

    def __init__(self) -> None:
        self._assistants: dict[int, UniversalAssistant] = {}

    def get(
        self, chat_id: int, bot_username: str = "", bot_name: str = ""
    ) -> UniversalAssistant:
        if chat_id not in self._assistants:
            self._assistants[chat_id] = get_telegram_assistant(bot_username, bot_name)
        return self._assistants[chat_id]

    def reset(self, chat_id: int) -> None:
        self._assistants.pop(chat_id, None)


registry = AssistantRegistry()
