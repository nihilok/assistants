import pytest
from unittest.mock import MagicMock, patch, AsyncMock


from assistants.ai.types import (
    AssistantInterface,
    MessageData,
)
from assistants.cli.io_loop import io_loop, io_loop_async, AssistantIoHandler


@pytest.fixture
def mock_assistant():
    assistant = MagicMock(spec=AssistantInterface)
    assistant.converse = AsyncMock()
    assistant.async_get_conversation_id = AsyncMock()
    return assistant


@pytest.fixture
def mock_message():
    message = MagicMock(spec=MessageData)
    message.text_content = "AI response"
    message.thread_id = "thread-id"
    return message


@pytest.fixture
def setup_assistant(mock_assistant, mock_message):
    mock_assistant.converse.return_value = mock_message
    mock_assistant.async_get_conversation_id.return_value = "new-thread-id"
    return mock_assistant


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.AssistantIoHandler.process_input")
@pytest.mark.asyncio
async def test_io_loop_async_with_initial_input(
    mock_process_input, mock_output, mock_get_input, setup_assistant
):
    # Setup to exit after processing initial input
    mock_get_input.return_value = "exit"
    mock_process_input.side_effect = [
        False,
        True,
    ]  # First call returns False, second call returns True (exit)

    # Call the function with initial input
    await io_loop_async(setup_assistant, "initial input", "thread-id")

    # Verify user input was displayed
    mock_output.user_input.assert_called_once_with("initial input")

    # Verify process_input was called with initial input
    mock_process_input.assert_any_call("initial input")
    assert (
        mock_process_input.call_count == 2
    )  # Called once for initial input, once for "exit"


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.AssistantIoHandler.process_input")
@pytest.mark.asyncio
async def test_io_loop_async_with_user_input(
    mock_process_input, mock_output, mock_get_input, setup_assistant
):
    # Setup to provide one input then exit
    mock_get_input.side_effect = ["user input", "exit"]
    mock_process_input.side_effect = [
        False,
        True,
    ]  # First call returns False, second call returns True (exit)

    # Call the function without initial input
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify process_input was called with user input
    mock_process_input.assert_any_call("user input")
    assert (
        mock_process_input.call_count == 2
    )  # Called once for user input, once for "exit"


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.AssistantIoHandler.process_input")
@pytest.mark.asyncio
async def test_io_loop_async_with_empty_input(
    mock_process_input, mock_output, mock_get_input, setup_assistant
):
    # Setup to provide empty input then exit
    mock_get_input.side_effect = ["", "exit"]
    mock_process_input.side_effect = [
        False,
        True,
    ]  # First call returns False, second call returns True (exit)

    # Call the function without initial input
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify process_input was called with empty input
    mock_process_input.assert_any_call("")
    assert (
        mock_process_input.call_count == 2
    )  # Called once for empty input, once for "exit"


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.AssistantIoHandler._handle_command")
@patch("assistants.cli.io_loop.AssistantIoHandler.process_input")
@pytest.mark.asyncio
async def test_io_loop_async_with_command(
    mock_process_input,
    mock_handle_command,
    mock_output,
    mock_get_input,
    setup_assistant,
):
    # Setup to provide command then exit
    mock_get_input.side_effect = ["/command arg1 arg2", "exit"]
    mock_process_input.side_effect = [
        False,
        True,
    ]  # First call returns False, second call returns True (exit)

    # Call the function
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify process_input was called with command
    mock_process_input.assert_any_call("/command arg1 arg2")
    assert (
        mock_process_input.call_count == 2
    )  # Called once for command, once for "exit"


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.AssistantIoHandler.process_input")
@pytest.mark.asyncio
async def test_io_loop_async_with_invalid_command(
    mock_process_input, mock_output, mock_get_input, setup_assistant
):
    # Setup to provide invalid command then exit
    mock_get_input.side_effect = ["/invalid", "exit"]
    mock_process_input.side_effect = [
        False,
        True,
    ]  # First call returns False, second call returns True (exit)

    # Call the function
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify process_input was called with invalid command
    mock_process_input.assert_any_call("/invalid")
    assert (
        mock_process_input.call_count == 2
    )  # Called once for invalid command, once for "exit"


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_assistant_io_handler_conversation(
    mock_output, setup_assistant, mock_message
):
    # Create handler
    handler = AssistantIoHandler(setup_assistant, "thread-id")
    handler.user_input = "Hello AI"

    # Call the method
    await handler._handle_conversation()

    # Verify assistant.converse was called with correct parameters
    setup_assistant.converse.assert_called_once_with("Hello AI", "thread-id")

    # Verify output was displayed
    mock_output.default.assert_called_once()

    # Verify conversation state was saved
    setup_assistant.async_get_conversation_id.assert_called_once()

    # Verify handler state was updated
    assert handler.last_message == mock_message
    assert handler.thread_id == "new-thread-id"


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_assistant_io_handler_with_last_message(mock_output, setup_assistant):
    # Create handler with last message
    handler = AssistantIoHandler(setup_assistant, "thread-id")
    handler.user_input = "Hello AI"

    # Setup last message
    last_message = MagicMock()
    last_message.thread_id = "last-thread-id"
    handler.last_message = last_message

    # Call the method
    await handler._handle_conversation()

    # Verify assistant.converse was called with last_message.thread_id
    setup_assistant.converse.assert_called_once_with("Hello AI", "last-thread-id")


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_assistant_io_handler_no_response(mock_output, setup_assistant):
    # Setup assistant to return None
    setup_assistant.converse.return_value = None

    # Create handler
    handler = AssistantIoHandler(setup_assistant, "thread-id")
    handler.user_input = "Hello AI"

    # Call the method
    await handler._handle_standard_conversation("thread-id")

    # Verify warning was displayed
    mock_output.warn.assert_called_once_with("No response from the AI model.")


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_assistant_io_handler_empty_response(mock_output, setup_assistant):
    # Setup assistant to return message with empty content
    message = MagicMock(spec=MessageData)
    message.text_content = ""
    setup_assistant.converse.return_value = message

    # Create handler
    handler = AssistantIoHandler(setup_assistant, "thread-id")
    handler.user_input = "Hello AI"

    # Call the method
    await handler._handle_standard_conversation("thread-id")

    # Verify warning was displayed
    mock_output.warn.assert_called_once_with("No response from the AI model.")


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_assistant_io_handler_duplicate_response(
    mock_output, setup_assistant, mock_message
):
    # Setup last message with same content as new message
    last_message = MagicMock(spec=MessageData)
    last_message.text_content = "AI response"

    # Create handler
    handler = AssistantIoHandler(setup_assistant, "thread-id")
    handler.user_input = "Hello AI"
    handler.last_message = last_message

    # Call the method
    await handler._handle_standard_conversation("thread-id")

    # Verify warning was displayed
    mock_output.warn.assert_called_once_with("No response from the AI model.")


@patch("assistants.cli.io_loop.highlight_code_blocks")
@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_assistant_io_handler_with_code_blocks(
    mock_output, mock_highlight, setup_assistant, mock_message
):
    # Setup highlight to return formatted text
    mock_highlight.return_value = "formatted response"

    # Create handler
    handler = AssistantIoHandler(setup_assistant, "thread-id")
    handler.user_input = "Hello AI"

    # Call the method
    await handler._handle_standard_conversation("thread-id")

    # Verify highlight_code_blocks was called
    mock_highlight.assert_called_once_with("AI response")

    # Verify formatted output was displayed
    mock_output.default.assert_called_once_with("formatted response")


@patch("assistants.cli.io_loop.io_loop_async")
@patch("asyncio.run")
def test_io_loop(mock_asyncio_run, mock_io_loop_async, setup_assistant):
    # Call the function
    io_loop(setup_assistant, "initial input", "thread-id")

    # Verify asyncio.run was called with io_loop_async
    mock_asyncio_run.assert_called_once()

    # Verify io_loop_async was called with correct parameters
    mock_io_loop_async.assert_called_once_with(
        setup_assistant, "initial input", "thread-id"
    )
