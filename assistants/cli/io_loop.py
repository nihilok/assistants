"""
This module contains the main input/output loop for interacting with the assistant.
"""
import asyncio
import re
from typing import Optional

import pyperclip
from openai.types.beta.threads import Message
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from assistants.ai.assistant import Completion, AssistantProtocol
from assistants.cli import output
from assistants.cli.constants import IO_INSTRUCTIONS
from assistants.cli.terminal import clear_screen
from assistants.cli.utils import get_text_from_default_editor, highlight_code_blocks
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


# Bind CTRL+L to clear the screen
@bindings.add("c-l")
def _(_event):
    clear_screen()


def io_loop(  # pylint: disable=too-many-branches too-many-statements
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
    is_completion = isinstance(assistant, Completion)

    def get_user_input() -> str:
        """
        Get user input from the prompt.

        :return: The user input as a string.
        """
        return prompt(PROMPT, style=style, history=history)

    while initial_input or (user_input := get_user_input()).lower() not in {
        "q",
        "quit",
        "exit",
    }:
        output.reset()
        if initial_input:
            output.user_input(initial_input)
            user_input = initial_input
            initial_input = ""

        if not user_input.strip():
            continue

        user_input = user_input.strip()

        match user_input.lower().strip():
            case instruction if instruction in {"-h", "--help", "help"}:
                output.inform(IO_INSTRUCTIONS)
                continue
            case "-e":
                user_input = get_text_from_default_editor().strip()
                if not user_input:
                    continue
                output.user_input(user_input)
            case "-c":
                if is_completion:
                    previous_response = assistant.memory[-1]["content"]  # type: ignore

                elif not last_message:
                    previous_response = ""
                else:
                    previous_response = last_message.content[0].text.value  # type: ignore

                if not previous_response:
                    output.warn("No previous message to copy.")
                    continue

                try:
                    pyperclip.copy(previous_response)
                except pyperclip.PyperclipException:
                    output.fail(
                        "Error copying to clipboard; this feature doesn't seem to be "
                        "available in the current terminal environment."
                    )
                    continue

                output.inform("Copied response to clipboard")
                continue
            case "-cb":
                if is_completion:
                    previous_response = assistant.memory[-1]["content"]  # type: ignore

                elif not last_message:
                    previous_response = ""
                else:
                    previous_response = last_message.content[0].text.value  # type: ignore

                if not previous_response:
                    output.warn("No previous message to copy from.")
                    continue

                code_blocks = re.split(
                    r"(```.*?```)", previous_response, flags=re.DOTALL
                )
                code_only = [
                    "\n".join(block.split("\n")[1:-1]).strip()
                    for block in code_blocks
                    if block.startswith("```")
                ]

                if not code_only:
                    output.warn("No codeblocks in previous message!")
                    continue

                all_code = "\n\n".join(code_only)

                try:
                    pyperclip.copy(all_code)
                except pyperclip.PyperclipException:
                    output.fail(
                        "Error copying code to clipboard; this feature doesn't seem to "
                        "be available in the current terminal environment."
                    )
                    continue

                output.inform("Copied code blocks to clipboard")
                continue
            case "-n":
                thread_id = None
                last_message = None
                clear_screen()
                continue
            case "clear":
                clear_screen()
                continue
            case nothing if not nothing:
                continue

        asyncio.run(converse(assistant, user_input, last_message, thread_id))


async def converse(
    assistant: AssistantProtocol,
    user_input: str = "",
    last_message: Optional[Message] = None,
    thread_id: Optional[str] = None,
):
    """
    Handle the conversation with the assistant.

    :param assistant: The assistant instance implementing AssistantProtocol.
    :param user_input: The user's input message.
    :param last_message: The last message in the conversation thread.
    :param thread_id: The ID of the conversation thread.
    """
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
