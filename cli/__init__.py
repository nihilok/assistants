import sys

from cli import output
from lib.exceptions import ConfigError

try:
    import config
except ConfigError as e:
    import re

    pattern = re.compile(r"Missing required (\w+) environment variable")

    match = pattern.match(str(e))

    output.fail(
        f"`{match.group(1)}` not found! Check README.md for setup instructions. Exiting..."
    )
    sys.exit(1)

import asyncio
import re
import sys
from pathlib import Path
from typing import Optional, Union, cast

import pyperclip  # type: ignore
from openai.types.beta.threads import Message
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from ai.assistant import Assistant, Completion
from cli.arg_parser import get_args
from cli.terminal import clear_screen
from cli.utils import (
    PERSISTENT_THREAD_ID_FILE,
    get_text_from_default_editor,
    get_thread_id,
    highlight_code_blocks,
)
from lib.exceptions import NoResponseError

bindings = KeyBindings()
history = FileHistory(f"{Path.home()}/.ai-assistant-history")
style = Style.from_dict(
    {"": "ansigreen", "input": "ansibrightgreen"},
)
message = [("class:input", ">>> ")]


IO_INSTRUCTIONS = """\
-h, --help:   Show this help message
-e:           Open the default editor to compose a prompt
-c:           Copy the previous response to the clipboard
-cb:          Copy the code blocks from the previous response to the clipboard
-n:           Start a new thread and clear the terminal screen
clear:        (or CTRL+L) Clear the terminal screen without starting a new thread"""


@bindings.add("c-l")
def _(event):
    clear_screen()


def _io_loop(
    assistant: Union[Assistant, Completion],
    initial_input: str = "",
    last_message: Optional[Message] = None,
    thread_id: Optional[str] = None,
):
    user_input = ""
    is_completion = isinstance(assistant, Completion)

    def get_user_input() -> str:
        global message
        return prompt(message, style=style, history=history)  # type: ignore

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

        else:
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

        message = asyncio.run(
            assistant.converse(
                initial_input or user_input,
                last_message.thread_id if last_message else thread_id,
            )
        )

        if message is None:
            output.warn("No response from the AI model.")
            continue

        if is_completion:
            output.default(message.content)  # type: ignore
            output.new_line(2)
            continue

        message = cast(Message, message)
        if last_message and message and message.id == last_message.id:
            raise NoResponseError

        text = highlight_code_blocks(message.content[0].text.value)

        output.default(text)
        output.new_line(2)
        last_message = message

        if last_message and not thread_id:
            with open(PERSISTENT_THREAD_ID_FILE, "w") as file:
                file.write(last_message.thread_id)


def cli():
    last_message = None
    thread_id = None

    args = get_args()

    instructions = (
        args.instructions if args.instructions else config.ASSISTANT_INSTRUCTIONS
    )
    initial_input = " ".join(args.positional_args) if args.positional_args else None

    if args.continue_thread:
        thread_id = get_thread_id()
        if thread_id is None:
            output.warn(
                "Warning: could not read last thread id from "
                f"'{PERSISTENT_THREAD_ID_FILE}' - starting new thread."
            )
    output.default(
        f"AI Assistant v{config.__VERSION__}; type 'help' for a list of commands.\n"
    )
    if args.editor:
        # Open the default editor to compose formatted prompt
        initial_input = get_text_from_default_editor(initial_input)
    elif args.input_file:
        # Read the initial prompt from a file
        try:
            with open(args.f, "r") as file:
                initial_input = file.read()
        except FileNotFoundError:
            output.fail(f"Error: The file '{args.f}' was not found.")
            sys.exit(1)

    # Create the assistant
    if args.code:
        assistant = Completion(model=config.CODE_MODEL)
    else:
        assistant = Assistant(
            "AI Assistant",
            config.DEFAULT_MODEL,
            instructions,
            tools=[{"type": "code_interpreter"}],
        )

    # IO Loop
    try:
        _io_loop(assistant, initial_input, last_message, thread_id)
    except (EOFError, KeyboardInterrupt):
        # Exit gracefully if ctrl+C or ctrl+D are pressed
        sys.exit(0)
