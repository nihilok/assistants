"""
This module contains the main input/output loop for interacting with the assistant.
"""
import asyncio
from dataclasses import dataclass
from typing import Optional

from openai.types.beta.threads import Message
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from assistants.ai.assistant import Completion, AssistantProtocol
from assistants.cli import output
from assistants.cli.commands import (
    COMMAND_MAP,
)
from assistants.cli.terminal import clear_screen
from assistants.cli.utils import highlight_code_blocks
from assistants.config.file_management import CONFIG_DIR
from assistants.lib.exceptions import NoResponseError
from assistants.user_data.sqlite_backend.threads import save_thread_data

bindings = KeyBindings()

# Prompt history
history = FileHistory(f"{CONFIG_DIR}/history")

# Styling for the prompt_toolkit prompt
style = Style.from_dict(
    {
        "": "ansigreen",  # green user input
        "input": "ansibrightgreen",  # bright green prompt symbol
    },
)
PROMPT = [("class:input", ">>> ")]  # prompt symbol


@dataclass
class IoEnviron:
    """
    Environment variables for the input/output loop.
    """

    assistant: AssistantProtocol
    last_message: Optional[Message] = None
    thread_id: Optional[str] = None


# Bind CTRL+L to clear the screen
@bindings.add("c-l")
def _(_event):
    clear_screen()


def io_loop(
    assistant: AssistantProtocol,
    initial_input: str = "",
    last_message: Optional[Message] = None,
    thread_id: Optional[str] = None,
):
    """
    Main input/output loop for interacting with the assistant.

    :param assistant: The assistant instance implementing AssistantProtocol.
    :param initial_input: Initial user input to start the conversation.
    :param last_message: The last message in the conversation thread.
    :param thread_id: The ID of the conversation thread.
    """
    user_input = ""

    def get_user_input() -> str:
        """
        Get user input from the prompt.

        :return: The user input as a string.
        """
        return prompt(PROMPT, style=style, history=history)

    environ = IoEnviron(
        assistant=assistant,
        last_message=last_message,
        thread_id=thread_id,
    )
    while initial_input or (user_input := get_user_input()).lower() not in {
        "q",
        "quit",
        "exit",
    }:
        output.reset()
        if initial_input:
            output.user_input(initial_input)
            user_input = initial_input

        if not user_input.strip():
            continue

        user_input = user_input.strip()

        # Handle commands
        command = COMMAND_MAP.get(user_input.lower())
        if command:
            command(environ)
            continue

        asyncio.run(converse(user_input, environ))


async def converse(
    user_input: str = "",
    environ: IoEnviron = None,
):
    """
    Handle the conversation with the assistant.

    :param user_input: The user's input message.
    :param environ: The environment variables manipulated on each
    iteration of the input/output loop.
    """
    assistant = environ.assistant
    last_message = environ.last_message
    thread_id = environ.thread_id

    message = await assistant.converse(
        user_input,
        last_message.thread_id if last_message else thread_id,
    )

    if message is None:
        output.warn("No response from the AI model.")
        return

    if isinstance(assistant, Completion):
        output.default(message.content)  # type: ignore
        output.new_line(2)
        return

    if last_message and message and message.id == last_message.id:
        raise NoResponseError

    text = highlight_code_blocks(message.content[0].text.value)

    output.default(text)
    output.new_line(2)
    last_message = message

    if last_message and not thread_id:
        thread_id = last_message.thread_id
        await save_thread_data(thread_id, assistant.assistant_id)
