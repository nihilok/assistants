import argparse
import os
import re
import sys

import pyperclip

from bot.ai.assistant import Assistant
from bot.config.environment import DEFAULT_MODEL, ASSISTANT_INSTRUCTIONS
from bot.exceptions import NoResponseError
from bot.helpers import get_text_from_default_editor


class TerminalColours:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


PERSISTENT_THREAD_ID_FILE = f"{os.environ.get('HOME', '.')}/.assistant-last-thread-id"


def cli():
    user_input = ""
    initial_input = ""
    last_message = None

    parser = argparse.ArgumentParser(description="CLI for AI Assistant")

    parser.add_argument(
        "-e", action="store_true", help="Open the default editor to compose a prompt."
    )
    parser.add_argument(
        "-f",
        metavar="INPUT_FILE",
        type=str,
        help="Read the initial prompt from a file (e.g., 'input.txt').",
    )
    parser.add_argument(
        "-s",
        metavar="INSTRUCTIONS",
        type=str,
        help="Read the initial system message / instructions from a specified file "
        "(if not provided, defaults will be used).",
    )
    parser.add_argument(
        "-t",
        action="store_true",
        help="Continue previous thread.",
    )
    parser.add_argument(
        "positional_args",
        nargs="*",
        help="Positional arguments to concatenate into a single prompt. E.g. ./cli.py This is a single prompt.",
    )

    args = parser.parse_args()

    instructions = args.s if args.s else ASSISTANT_INSTRUCTIONS

    thread_id = None
    if args.t:
        try:
            with open(PERSISTENT_THREAD_ID_FILE, "r") as f:
                thread_id = f.read().strip("\n")
        except FileNotFoundError:
            print(
                "Warning: could not read last thread id from ~/.assistant-last-thread-id - starting new thread..."
            )

    if args.e:
        # Open the default editor to compose formatted prompt
        if args.positional_args:
            # If text was provided as positional args alongside the `-e` option, concatenate to a single string and
            # we can pre-populate the editor (or rather the temp file used by the editor) with this text.
            initial_cli_input = " ".join(args.positional_args)
        else:
            initial_cli_input = None
        initial_input = get_text_from_default_editor(initial_cli_input)
    elif args.f:
        # Read the initial prompt from a file
        try:
            with open(args.f, "r") as file:
                initial_input = file.read()
        except FileNotFoundError:
            print(f"Error: The file '{args.f}' was not found.")
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
            user_input := input(TerminalColours.OKGREEN + ">>> ")
        ).lower() not in {"q", "quit", "exit"}:
            if initial_input:
                print(TerminalColours.OKGREEN + ">>> " + initial_input)
                user_input = initial_input

            if not user_input.strip():
                continue

            else:
                user_input = user_input.strip()

            if user_input.lower() == "-e":
                user_input = get_text_from_default_editor()
                print(user_input)
            elif user_input.lower() == "-c":
                if not last_message:
                    print(
                        TerminalColours.WARNING
                        + "No previous message to copy from."
                        + TerminalColours.ENDC
                    )
                    continue
                previous_response = last_message.content[0].text.value
                pyperclip.copy(previous_response)
                print(TerminalColours.OKBLUE + "Copied response to clipboard")
                continue
            elif user_input.lower() == "-cb":
                if not last_message:
                    print(
                        TerminalColours.WARNING
                        + "No previous message to copy from."
                        + TerminalColours.ENDC
                    )
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
                    print(
                        TerminalColours.WARNING
                        + "No codeblocks in previous message."
                        + TerminalColours.ENDC
                    )
                    continue

                all_code = "\n\n".join(code_only)
                pyperclip.copy(all_code)
                print(TerminalColours.OKBLUE + "Copied code blocks to clipboard")
                continue

            print(TerminalColours.ENDC, end="")
            message = assistant.converse(
                initial_input or user_input,
                last_message.thread_id if last_message else thread_id,
            )

            initial_input = ""  # Only relevant for first iteration (comes from initial command line),
            # resetting to empty string here, so it won't be evaluated as truthy in future iterations

            if last_message and message.id == last_message.id:
                raise NoResponseError

            print(message.content[0].text.value, end="\n\n")
            last_message = message

            if not thread_id:
                with open(PERSISTENT_THREAD_ID_FILE, "w") as file:
                    file.write(last_message.thread_id)

    except (EOFError, KeyboardInterrupt):
        # Exit gracefully if ctrl+C or ctrl+D are pressed
        sys.exit(0)
