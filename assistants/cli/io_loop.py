"""
This module contains the main input/output loop for interacting with the assistant.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from assistants.ai.memory import MemoryMixin
from assistants.ai.types import AssistantProtocol
from assistants.cli import output
from assistants.cli.commands import COMMAND_MAP, EXIT_COMMANDS, IoEnviron
from assistants.cli.terminal import clear_screen
from assistants.cli.utils import highlight_code_blocks
from assistants.config.file_management import CONFIG_DIR
from assistants.log import logger


# Constants and Configuration
class PromptStyle(Enum):
    USER_INPUT = "ansigreen"
    PROMPT_SYMBOL = "ansibrightgreen"


INPUT_CLASSNAME = "input"


@dataclass
class PromptConfig:
    style: Style = Style.from_dict(
        {
            "": PromptStyle.USER_INPUT.value,
            INPUT_CLASSNAME: PromptStyle.PROMPT_SYMBOL.value,
        }
    )
    prompt_symbol: str = ">>>"
    history_file: str = f"{CONFIG_DIR}/history"


# Setup
bindings = KeyBindings()
config = PromptConfig()
history = FileHistory(config.history_file)
PROMPT = [(f"class:{INPUT_CLASSNAME}", f"{config.prompt_symbol} ")]


# Bind CTRL+L to clear the screen
@bindings.add("c-l")
def _(_event):
    clear_screen()


def get_user_input() -> str:
    """Get user input from interactive/styled prompt (prompt_toolkit)."""
    return prompt(PROMPT, style=config.style, history=history, in_thread=True)


async def io_loop_async(
    assistant: AssistantProtocol | MemoryMixin,
    initial_input: str = "",
    thread_id: Optional[str] = None,
):
    """
    Main input/output loop for interacting with the assistant.

    :param assistant: The assistant instance implementing AssistantProtocol.
    :param initial_input: Initial user input to start the conversation.
    :param thread_id: The ID of the conversation thread.
    """
    environ = IoEnviron(
        assistant=assistant,
        thread_id=thread_id,
    )
    while (
        initial_input or (user_input := get_user_input()).lower() not in EXIT_COMMANDS
    ):
        output.reset()
        environ.user_input = None
        if initial_input:
            output.user_input(initial_input)
            user_input = initial_input
            initial_input = ""  # Otherwise, the initial input will be repeated in the next iteration

        user_input = user_input.strip()

        if not user_input:
            continue

        # Handle commands
        c, *args = user_input.split(" ")
        command = COMMAND_MAP.get(c.lower())
        if command:
            logger.debug(
                f"Command input: {user_input}; Command: {command.__class__.__name__}"
            )
            await command(environ, *args)
            if environ.user_input:
                initial_input = environ.user_input
            continue

        environ.user_input = user_input
        await converse(environ)


async def converse(
    environ: IoEnviron,
):
    """
    Handle the conversation with the assistant.

    :param environ: The environment variables manipulated on each
    iteration of the input/output loop.
    """
    assistant = environ.assistant
    last_message = environ.last_message
    thread_id = environ.thread_id  # Could be None; a new thread will be created if so.

    message = await assistant.converse(
        environ.user_input, last_message.thread_id if last_message else thread_id
    )

    if (
        message is None
        or not message.text_content
        or last_message
        and last_message.text_content == message.text_content
    ):
        output.warn("No response from the AI model.")
        return

    text = highlight_code_blocks(message.text_content)

    output.default(text)
    output.new_line(2)

    # Set and save the new conversation state for future iterations:
    environ.last_message = message
    environ.thread_id = await assistant.save_conversation_state()


def io_loop(
    assistant: AssistantProtocol | MemoryMixin,
    initial_input: str = "",
    thread_id: Optional[str] = None,
):
    asyncio.run(io_loop_async(assistant, initial_input, thread_id))
