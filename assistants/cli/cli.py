"""
The CLI module is the entry point for the Assistant CLI.
It is responsible for parsing command line arguments, creating the Assistant object,
and starting the IO loop.
"""

import asyncio
import io
import select
import sys
from typing import Optional, Tuple

import setproctitle
import yaml

from assistants.ai.types import AssistantInterface
from assistants.cli import output
from assistants.cli.arg_parser import get_args
from assistants.cli.io_loop import io_loop
from assistants.cli.utils import (
    create_assistant_and_thread,
    display_welcome_message,
    get_text_from_default_editor,
)
from assistants.config import (
    environment,
    update_args_from_config_file,
)
from assistants.lib.exceptions import ConfigError


def run():
    """Run the CLI application."""
    cli = CLI()
    cli.run()


class CLI:
    """
    Class that maintains state and manages the IO loop for the Assistant CLI.
    """

    def __init__(self):
        """Initialise the CLI class with default state."""
        self.args = None
        self.assistant = None
        self.thread_id = None
        self.initial_input = ""

    @staticmethod
    def set_process_title():
        """Set the process title for the CLI."""
        setproctitle.setproctitle("assistant-cli")

    def parse_arguments(self):
        """Parse command line arguments."""
        self.args = get_args()

    def update_from_config(self):
        """Update environment and args from config file if provided."""
        if self.args.config_file:
            try:
                with open(self.args.config_file) as file:
                    config = yaml.safe_load(file)
                    environment.update_from_config_yaml(config)
                    update_args_from_config_file(config, self.args)
            except FileNotFoundError:
                output.fail(f"Error: The file '{self.args.config_file}' was not found.")
                sys.exit(1)
            except yaml.YAMLError as e:
                output.fail(f"Error: {e}")
                sys.exit(1)

    def validate_arguments(self):
        """Validate and prepare arguments."""
        if self.args.thinking and (self.args.thinking > 2 or self.args.thinking < 0):
            output.fail("Error: The 'thinking' level must be between 0 and 2.")
            sys.exit(1)

        # Set default model if not provided
        if not self.args.model:
            self.args.model = environment.DEFAULT_MODEL

    def prepare_initial_input(self):
        """Get the initial input from args."""
        # Check for stdin input
        try:
            if select.select([sys.stdin], [], [], 0.0)[0]:
                stdin = sys.stdin.read()
                if stdin:
                    self.args.prompt = self.args.prompt or []
                    self.args.prompt += stdin.split(" ")
        except (io.UnsupportedOperation, ValueError):
            # Skip stdin check if it's not available (e.g., in tests)
            pass

        # Join arguments into a single string
        initial_input = " ".join(self.args.prompt) if self.args.prompt else None

        # Handle editor mode
        if self.args.editor:
            self.initial_input = get_text_from_default_editor(initial_input)
            return

        # Handle input file
        if self.args.input_file:
            try:
                with open(self.args.input_file, "r", encoding="utf-8") as file:
                    self.initial_input = file.read()
            except FileNotFoundError:
                output.fail(f"Error: The file '{self.args.input_file}' was not found.")
                sys.exit(1)
            return

        self.initial_input = initial_input

    def show_welcome_message(self):
        """Display welcome message."""
        display_welcome_message(self.args)

    async def create_assistant(self) -> Tuple[AssistantInterface, Optional[str]]:
        """Create assistant and get the last thread if one exists."""
        return await create_assistant_and_thread(self.args, environment)

    def handle_conversation_status(self):
        """Handle thread status messages."""
        if self.thread_id is None and self.args.continue_thread:
            output.warn("Warning: could not read last thread id; starting new thread.")
        elif self.args.continue_thread:
            output.inform("Continuing previous thread...")

    def start_io_loop(self):
        """Start the IO loop."""
        try:
            io_loop(self.assistant, self.initial_input, thread_id=self.thread_id)
        except (EOFError, KeyboardInterrupt):
            # Exit gracefully if ctrl+C or ctrl+D are pressed
            sys.exit(0)

    def run(self):
        """Run the CLI application."""
        self.set_process_title()
        self.parse_arguments()
        self.update_from_config()
        self.validate_arguments()
        self.prepare_initial_input()
        self.show_welcome_message()

        # Create assistant and get the last thread if one exists
        try:
            self.assistant, self.thread_id = asyncio.run(self.create_assistant())
        except ConfigError as e:
            output.fail(f"Error: {e}")
            sys.exit(1)

        self.handle_conversation_status()
        self.start_io_loop()
