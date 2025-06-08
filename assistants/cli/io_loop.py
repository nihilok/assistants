"""
This module contains the main input/output loop for interacting with the assistant.
"""

import asyncio
from typing import Optional

from assistants.ai.types import AssistantInterface, StreamingAssistantInterface
from assistants.cli import output
from assistants.cli.commands import COMMAND_MAP, EXIT_COMMANDS, IoEnviron
from assistants.cli.prompt import get_user_input
from assistants.cli.utils import highlight_code_blocks
from assistants.log import logger
from assistants.cli.utils import StreamHighlighter


class AssistantIoHandler:
    """
    Handles IO operations and state management for assistant interactions.
    Encapsulates command processing, conversation management, and state transitions.
    """

    def __init__(self, assistant: AssistantInterface, thread_id: Optional[str] = None):
        self.assistant = assistant
        self.thread_id = thread_id
        self.last_message = None
        self.user_input = None
        self.is_streaming = isinstance(assistant, StreamingAssistantInterface)

    async def process_input(self, input_text: str) -> bool:
        """
        Process user input and return True if the program should exit.

        :param input_text: The text input from the user
        :return: True if program should exit, False otherwise
        """
        output.reset()
        self.user_input = input_text.strip()

        if not self.user_input:
            return False

        if self.user_input.lower() in EXIT_COMMANDS:
            return True

        if self.user_input.startswith("/"):
            await self._handle_command()
        else:
            await self._handle_conversation()

        return False

    async def _handle_command(self):
        """Process and execute a command."""
        c, *args = self.user_input.split(" ")
        command = COMMAND_MAP.get(c)
        if command:
            logger.debug(
                f"Command input: {self.user_input}; Command: {command.__class__.__name__}"
            )

            # Create a temporary IoEnviron for backward compatibility with existing commands
            environ = IoEnviron(
                assistant=self.assistant,
                thread_id=self.thread_id,
                last_message=self.last_message,
                user_input=None,
            )

            await command(environ, *args)

            # Update our state from the environ
            self.thread_id = environ.thread_id
            self.last_message = environ.last_message

            # If command set user_input, it wants to continue with that as input
            if environ.user_input:
                self.user_input = environ.user_input
                await self._handle_conversation()
        else:
            output.warn("Invalid command!")

    async def _handle_conversation(self):
        """Handle conversation with the assistant (streaming or non-streaming)."""
        thread_id_to_use = (
            self.last_message.thread_id if self.last_message else self.thread_id
        )

        if self.is_streaming:
            await self._handle_streaming_conversation(thread_id_to_use)
        else:
            await self._handle_standard_conversation(thread_id_to_use)

        # Save conversation state for future interactions
        self.thread_id = await self.assistant.save_conversation_state()
        output.new_line(2)

    async def _handle_streaming_conversation(self, thread_id_to_use):
        """Handle streaming conversation with real-time highlighting."""
        full_text = ""
        highlighter = StreamHighlighter()

        if not isinstance(self.assistant, StreamingAssistantInterface):
            output.warn("Streaming is not supported by this assistant.")
            return

        async for chunk in self.assistant.stream_converse(
            self.user_input, thread_id_to_use
        ):
            full_text += chunk
            highlighted_chunk = highlighter.process_chunk(chunk)
            if highlighted_chunk:
                output.default(highlighted_chunk)

        # Process any remaining text in buffer
        final_chunk = highlighter.finalise()
        if final_chunk:
            output.default(final_chunk)

        if full_text:
            # Create message object for history
            message_data = await self.assistant.get_last_message(thread_id_to_use or "")
            if message_data:
                self.last_message = message_data
            else:
                # If we couldn't get a proper message object, create one
                from assistants.ai.types import MessageData

                self.last_message = MessageData(
                    thread_id=thread_id_to_use or "", text_content=full_text
                )
        else:
            output.warn("No response from the AI model.")

    async def _handle_standard_conversation(self, thread_id_to_use):
        """Handle standard non-streaming conversation."""
        message = await self.assistant.converse(self.user_input, thread_id_to_use)

        if (
            message is None
            or not message.text_content
            or (
                self.last_message
                and self.last_message.text_content == message.text_content
            )
        ):
            output.warn("No response from the AI model.")
            return

        text = highlight_code_blocks(message.text_content)
        output.default(text)
        self.last_message = message


async def io_loop_async(assistant, initial_input, thread_id):
    handler = AssistantIoHandler(assistant, thread_id)

    if initial_input:
        output.user_input(initial_input)
        await handler.process_input(initial_input)

    while True:
        user_input = get_user_input()
        should_exit = await handler.process_input(user_input)
        if should_exit:
            break


def io_loop(
    assistant: AssistantInterface,
    initial_input: str = "",
    thread_id: Optional[str] = None,
):
    asyncio.run(io_loop_async(assistant, initial_input, thread_id))
