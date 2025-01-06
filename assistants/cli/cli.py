"""
The CLI module is the entry point for the Assistant CLI.
It is responsible for parsing command line arguments, creating the Assistant object,
and starting the IO loop.
"""

import sys
import asyncio

import assistants.cli.commands
from assistants.cli import output
from assistants.cli.io_loop import io_loop
from assistants.lib.exceptions import ConfigError

try:
    from assistants.config import environment
except ConfigError as e:
    import re

    pattern = re.compile(r"Missing required (\w+) environment variable")

    match = pattern.match(str(e))

    if match is None:
        output.fail(f"Error: {e}")
        sys.exit(1)

    output.fail(
        f"`{match.group(1)}` not found! Check README.md for setup instructions. Exiting..."
    )
    sys.exit(1)


from assistants import version
from assistants.cli.arg_parser import get_args
from assistants.cli.utils import (
    get_text_from_default_editor,
    create_assistant_and_thread,
)


def cli():
    """
    Main function for the Assistant CLI.
    """

    # Parse command line arguments, if --help is passed, it will exit here
    args = get_args()

    # Join all the positional arguments into a single string
    initial_input = " ".join(args.prompt) if args.prompt else None

    # First line of output (version and basic instructions)
    output.default(
        f"Assistant CLI v{version.__VERSION__}; type 'help' for a list of commands.\n"
    )

    if args.editor:
        # Open the default editor to compose formatted prompt
        initial_input = get_text_from_default_editor(initial_input)

    elif args.input_file:
        # Read the initial prompt from a file
        try:
            with open(args.f, "r") as file:  # pylint: disable=unspecified-encoding
                initial_input = file.read()
        except FileNotFoundError:
            output.fail(f"Error: The file '{args.f}' was not found.")
            sys.exit(1)

    # Create assistant and get the last thread if one exists
    assistant, thread = asyncio.run(create_assistant_and_thread(args))

    if thread is None and args.continue_thread:
        output.warn("Warning: could not read last thread id; starting new thread.")
        thread_id = None
    elif thread is not None and args.continue_thread:
        thread_id = thread.thread_id
    else:
        thread_id = None

    # IO Loop (takes user input and sends it to the assistant, or parses it as a command,
    # then prints the response before looping to do it all over again)
    try:
        io_loop(assistant, initial_input, thread_id=thread_id)
    except (EOFError, KeyboardInterrupt):
        # Exit gracefully if ctrl+C or ctrl+D are pressed
        sys.exit(0)
