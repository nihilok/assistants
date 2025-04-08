"""
The CLI module is the entry point for the Assistant CLI.
It is responsible for parsing command line arguments, creating the Assistant object,
and starting the IO loop.
"""

import asyncio
import sys

import setproctitle

from assistants.cli import output
from assistants.cli.arg_parser import get_args
from assistants.cli.io_loop import io_loop
from assistants.cli.utils import (
    create_assistant_and_thread,
    read_config_file,
    get_initial_input,
    validate_args,
    display_welcome_message,
)
from assistants.config import (
    environment,
    update_args_from_config_file,
)
from assistants.lib.exceptions import ConfigError


def cli():
    """
    Main function (entrypoint) for the Assistant CLI.
    """
    setproctitle.setproctitle("assistant-cli")

    # Parse command line arguments
    args = get_args()

    # Update from config file if provided
    if args.config_file:
        config = read_config_file(args.config_file)
        environment.update_from_config_yaml(config)
        update_args_from_config_file(config, args)

    # Validate and prepare arguments
    args = validate_args(args)

    # Get the initial input
    initial_input = get_initial_input(args)

    # Display welcome message
    display_welcome_message(args)

    # Create assistant and get the last thread if one exists
    try:
        assistant, thread_id = asyncio.run(
            create_assistant_and_thread(args, environment)
        )
    except ConfigError as e:
        output.fail(f"Error: {e}")
        sys.exit(1)

    if thread_id is None and args.continue_thread:
        output.warn("Warning: could not read last thread id; starting new thread.")
    elif args.continue_thread:
        output.inform("Continuing previous thread...")

    # Start IO Loop
    try:
        io_loop(assistant, initial_input, thread_id=thread_id)
    except (EOFError, KeyboardInterrupt):
        # Exit gracefully if ctrl+C or ctrl+D are pressed
        sys.exit(0)
