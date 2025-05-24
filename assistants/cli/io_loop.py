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


async def io_loop_async(
    assistant: AssistantInterface,
    initial_input: str = "",
    thread_id: Optional[str] = None,
):
    """
    Main input/output loop for interacting with the assistant.

    :param assistant: The assistant instance implementing AssistantProtocol.
    :param initial_input: Initial user input to start the conversation.
    :param thread_id: The ID of the conversation thread.
    """
    environ = IoEnviron(
        assistant=assistant,
        thread_id=thread_id,
    )
    while (
        initial_input or (user_input := get_user_input()).lower() not in EXIT_COMMANDS
    ):
        output.reset()
        environ.user_input = None
        if initial_input:
            output.user_input(initial_input)
            user_input = initial_input
            initial_input = ""  # Otherwise, the initial input will be repeated in the next iteration

        user_input = user_input.strip()

        if not user_input:
            continue

        # Handle commands
        c, *args = user_input.split(" ")
        command = COMMAND_MAP.get(c.lower())
        if command:
            logger.debug(
                f"Command input: {user_input}; Command: {command.__class__.__name__}"
            )
            await command(environ, *args)
            if environ.user_input:
                initial_input = environ.user_input
            continue

        if user_input.startswith("/"):
            output.warn("Invalid command!")
            continue

        environ.user_input = user_input
        await converse(environ)


async def converse(environ: IoEnviron):
    """
    Handle the conversation with the assistant.

    :param environ: The environment variables manipulated on each
    iteration of the input/output loop.
    """
    assistant = environ.assistant
    last_message = environ.last_message
    thread_id = environ.thread_id  # Could be None; a new thread will be created if so.

    # Check if assistant supports streaming
    if isinstance(assistant, StreamingAssistantInterface):
        # Handle streaming conversation
        thread_id_to_use = last_message.thread_id if last_message else thread_id
        full_text = ""

        # Create stream highlighter for real-time syntax highlighting
        highlighter = StreamHighlighter()

        async for chunk in assistant.stream_converse(
            environ.user_input, thread_id_to_use
        ):
            full_text += chunk

            # Process and highlight the chunk in real-time
            highlighted_chunk = highlighter.process_chunk(chunk)
            if highlighted_chunk:
                output.default(highlighted_chunk)

        # Process any remaining text in buffer
        final_chunk = highlighter.finalize()
        if final_chunk:
            output.default(final_chunk)

        if full_text:
            # Create message object for history
            message_data = await assistant.get_last_message(thread_id_to_use or "")
            if message_data:
                environ.last_message = message_data
            else:
                # If we couldn't get a proper message object, create one
                from assistants.ai.types import MessageData

                environ.last_message = MessageData(
                    thread_id=thread_id_to_use or "", text_content=full_text
                )
        else:
            output.warn("No response from the AI model.")
            return
    else:
        # Non-streaming conversation (existing behavior)
        message = await assistant.converse(
            environ.user_input, last_message.thread_id if last_message else thread_id
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
        environ.last_message = message

    output.new_line(2)
    # Save the conversation state for future iterations
    environ.thread_id = await assistant.save_conversation_state()


def io_loop(
    assistant: AssistantInterface,
    initial_input: str = "",
    thread_id: Optional[str] = None,
):
    asyncio.run(io_loop_async(assistant, initial_input, thread_id))
