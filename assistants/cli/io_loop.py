"""
This module contains the main input/output loop for interacting with the assistant.
"""
import asyncio
from typing import Optional

from openai.types.beta.threads import Message
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from assistants.ai.memory import MemoryMixin
from assistants.ai.openai import Assistant
from assistants.ai.types import AssistantProtocol
from assistants.cli import output
from assistants.cli.commands import COMMAND_MAP, EXIT_COMMANDS, IoEnviron
from assistants.cli.terminal import clear_screen
from assistants.cli.utils import highlight_code_blocks
from assistants.config.file_management import CONFIG_DIR
from assistants.log import logger
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


# Bind CTRL+L to clear the screen
@bindings.add("c-l")
def _(_event):
    clear_screen()


def io_loop(
    assistant: AssistantProtocol | MemoryMixin,
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
    while (
        initial_input or (user_input := get_user_input()).lower() not in EXIT_COMMANDS
    ):
        output.reset()
        if initial_input:
            output.user_input(initial_input)
            user_input = initial_input
            initial_input = ""  # Otherwise, the initial input will be repeated in the next iteration

        if not user_input.strip():
            continue

        user_input = user_input.strip()

        # Handle commands
        command = COMMAND_MAP.get(user_input.lower())
        if command:
            logger.debug(
                f"Command input: {user_input}; Command: {command.__class__.__name__}"
            )
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
        user_input, last_message.thread_id if last_message else thread_id
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
    environ.last_message = message

    if (
        environ.last_message
        and not environ.thread_id
        and isinstance(assistant, Assistant)
    ):
        environ.thread_id = environ.last_message.thread_id
        await save_thread_data(environ.thread_id, assistant.assistant_id, user_input)
    elif not isinstance(assistant, Assistant):
        await assistant.save_conversation()
        environ.thread_id = assistant.conversation_id
