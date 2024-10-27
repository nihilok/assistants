import asyncio
import os
import re
import sys

import pyperclip

from bot.ai.assistant import Assistant
from bot.cli import output
from bot.cli.arg_parser import get_args
from bot.cli.terminal import clear_screen, ANSIEscapeSequence
from bot.config.environment import DEFAULT_MODEL, ASSISTANT_INSTRUCTIONS
from bot.exceptions import NoResponseError
from bot.helpers import get_text_from_default_editor

PERSISTENT_THREAD_ID_FILE = f"{os.environ.get('HOME', '.')}/.assistant-last-thread-id"


def cli():
    user_input = ""
    initial_input = ""
    last_message = None

    args = get_args()

    instructions = args.instructions if args.instructions else ASSISTANT_INSTRUCTIONS

    thread_id = None
    if args.t:
        try:
            with open(PERSISTENT_THREAD_ID_FILE, "r") as f:
                thread_id = f.read().strip("\n")
        except FileNotFoundError:
            output.warn(
                f"Warning: could not read last thread id from '{PERSISTENT_THREAD_ID_FILE}' - starting new thread..."
            )

    if args.editor:
        # Open the default editor to compose formatted prompt
        if args.positional_args:
            # If text was provided as positional args alongside the `-e` option, concatenate to a single string and
            # we can pre-populate the editor (or rather the temp file used by the editor) with this text.
            initial_cli_input = " ".join(args.positional_args)
        else:
            initial_cli_input = None
        initial_input = get_text_from_default_editor(initial_cli_input)
    elif args.input_file:
        # Read the initial prompt from a file
        try:
            with open(args.f, "r") as file:
                initial_input = file.read()
        except FileNotFoundError:
            output.fail(f"Error: The file '{args.f}' was not found.")
            sys.exit(1)
    elif args.positional_args:
        initial_input = " ".join(args.positional_args)

    # Create the assistant
    assistant = Assistant(
        "AI Assistant",
        DEFAULT_MODEL,
        instructions,
        tools=[{"type": "code_interpreter"}],
    )

    # IO Loop
    try:
        while initial_input or (
            user_input := input(ANSIEscapeSequence.OKGREEN + ">>> ")
        ).lower() not in {"q", "quit", "exit"}:
            output.reset()
            if initial_input:
                output.user_input(initial_input)
                user_input = initial_input

            if not user_input.strip():
                continue

            else:
                user_input = user_input.strip()

            if user_input.lower() == "-e":
                user_input = get_text_from_default_editor()
                output.user_input(user_input)
            elif user_input.lower() == "-c":
                if not last_message:
                    output.warn("No previous message to copy from.")
                    continue
                previous_response = last_message.content[0].text.value

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
            elif user_input.lower() == "-cb":
                if not last_message:
                    output.warn("No previous message to copy from!")
                    continue
                previous_response = last_message.content[0].text.value
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
                        "Error copying code to clipboard; this feature doesn't seem to be "
                        "available in the current terminal environment."
                    )
                    continue

                output.inform("Copied code blocks to clipboard")
                continue
            elif user_input.lower().strip() in {"-n", "clear"}:
                thread_id = None
                last_message = None
                clear_screen()
                continue

            message = asyncio.run(
                assistant.converse(
                    initial_input or user_input,
                    last_message.thread_id if last_message else thread_id,
                )
            )

            initial_input = ""  # Only relevant for first iteration (comes from initial command line),
            # resetting to empty string here, so it won't be evaluated as truthy in future iterations

            if last_message and message.id == last_message.id:
                raise NoResponseError

            output.default(message.content[0].text.value)
            output.new_line(2)
            last_message = message

            if not thread_id:
                with open(PERSISTENT_THREAD_ID_FILE, "w") as file:
                    file.write(last_message.thread_id)

    except (EOFError, KeyboardInterrupt):
        # Exit gracefully if ctrl+C or ctrl+D are pressed
        sys.exit(0)
