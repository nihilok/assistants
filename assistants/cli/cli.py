"""
The CLI module is the entry point for the Assistant CLI.
It is responsible for parsing command line arguments, creating the Assistant object,
and starting the IO loop.
"""

import asyncio
import sys

from assistants import version
from assistants.cli import output
from assistants.cli.arg_parser import get_args
from assistants.cli.io_loop import io_loop
from assistants.cli.utils import (
    create_assistant_and_thread,
    get_text_from_default_editor,
)
from assistants.config import environment
from assistants.lib.exceptions import ConfigError


def cli():
    """
    Main function (entrypoint) for the Assistant CLI.
    """

    # Parse command line arguments, if --help is passed, it will exit here
    args = get_args()

    # Join all the positional arguments into a single string
    initial_input = " ".join(args.prompt) if args.prompt else None

    # First line of output (version and basic instructions)
    output.default(
        f"""Assistant CLI v{version.__VERSION__}; using '{environment.CODE_MODEL if args.code else environment.DEFAULT_MODEL}' model{' (reasoning model)' if args.code else ''}.
Type '/help' (or '/h') for a list of commands.
"""
    )
    output.default("")
    if args.editor:
        # Open the default editor to compose formatted prompt
        initial_input = get_text_from_default_editor(initial_input)

    elif args.input_file:
        # Read the initial prompt from a file
        try:
            with open(  # pylint: disable=unspecified-encoding
                args.input_file, "r"
            ) as file:
                initial_input = file.read()
        except FileNotFoundError:
            output.fail(f"Error: The file '{args.input_file}' was not found.")
            sys.exit(1)

    # Create assistant and get the last thread if one exists
    try:
        assistant, thread_id = asyncio.run(create_assistant_and_thread(args))
    except ConfigError as e:
        output.fail(f"Error: {e}")
        sys.exit(1)

    if thread_id is None and args.continue_thread:
        output.warn("Warning: could not read last thread id; starting new thread.")

    # IO Loop (takes user input and sends it to the assistant, or parses it as a command,
    # then prints the response before looping to do it all over again)
    try:
        io_loop(assistant, initial_input, thread_id=thread_id)
    except (EOFError, KeyboardInterrupt):
        # Exit gracefully if ctrl+C or ctrl+D are pressed
        sys.exit(0)
