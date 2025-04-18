import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


from assistants.ai.types import AssistantInterface, MessageData
from assistants.cli.commands import IoEnviron
from assistants.cli.io_loop import io_loop, io_loop_async, converse


@pytest.fixture
def mock_assistant():
    assistant = MagicMock(spec=AssistantInterface)
    assistant.converse = AsyncMock()
    assistant.save_conversation_state = AsyncMock()
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
    mock_assistant.save_conversation_state.return_value = "new-thread-id"
    return mock_assistant


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.converse")
@pytest.mark.asyncio
async def test_io_loop_async_with_initial_input(
    mock_converse, mock_output, mock_get_input, setup_assistant
):
    # Setup to exit after processing initial input
    mock_get_input.return_value = "exit"

    # Call the function with initial input
    await io_loop_async(setup_assistant, "initial input", "thread-id")

    # Verify output was reset
    mock_output.reset.assert_called_once()

    # Verify user input was displayed
    mock_output.user_input.assert_called_once_with("initial input")

    # Verify converse was called with correct parameters
    environ_arg = mock_converse.call_args[0][0]
    assert environ_arg.assistant == setup_assistant
    assert environ_arg.thread_id == "thread-id"
    assert environ_arg.user_input == "initial input"


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.converse")
@pytest.mark.asyncio
async def test_io_loop_async_with_user_input(
    mock_converse, mock_output, mock_get_input, setup_assistant
):
    # Setup to provide one input then exit
    mock_get_input.side_effect = ["user input", "exit"]

    # Call the function without initial input
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify converse was called with correct parameters
    environ_arg = mock_converse.call_args[0][0]
    assert environ_arg.assistant == setup_assistant
    assert environ_arg.thread_id == "thread-id"
    assert environ_arg.user_input == "user input"


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_io_loop_async_with_empty_input(
    mock_output, mock_get_input, setup_assistant
):
    # Setup to provide empty input then exit
    mock_get_input.side_effect = ["", "exit"]

    # Call the function without initial input
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify that no converse call was made (we continue the loop on empty input)
    setup_assistant.converse.assert_not_called()


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@patch("assistants.cli.io_loop.COMMAND_MAP")
@pytest.mark.asyncio
async def test_io_loop_async_with_command(
    mock_command_map, mock_output, mock_get_input, setup_assistant
):
    # Setup command
    mock_command = AsyncMock()
    mock_command_map.get.return_value = mock_command

    # Setup to provide command then exit
    mock_get_input.side_effect = ["/command arg1 arg2", "exit"]

    # Call the function
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify command was looked up and called
    mock_command_map.get.assert_called_once_with("/command")
    mock_command.assert_called_once()

    # Verify args were passed correctly
    environ_arg = mock_command.call_args[0][0]
    assert environ_arg.assistant == setup_assistant
    assert environ_arg.thread_id == "thread-id"
    assert mock_command.call_args[0][1:] == ("arg1", "arg2")


@patch("assistants.cli.io_loop.get_user_input")
@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_io_loop_async_with_invalid_command(
    mock_output, mock_get_input, setup_assistant
):
    # Setup to provide invalid command then exit
    mock_get_input.side_effect = ["/invalid", "exit"]

    # Call the function
    await io_loop_async(setup_assistant, "", "thread-id")

    # Verify warning was displayed
    mock_output.warn.assert_called_once_with("Invalid command!")


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_converse_success(mock_output, setup_assistant, mock_message):
    # Setup environment
    environ = IoEnviron(
        assistant=setup_assistant, thread_id="thread-id", user_input="Hello AI"
    )

    # Call the function
    await converse(environ)

    # Verify assistant.converse was called with correct parameters
    setup_assistant.converse.assert_called_once_with("Hello AI", "thread-id")

    # Verify output was displayed
    mock_output.default.assert_called_once()

    # Verify conversation state was saved
    setup_assistant.save_conversation_state.assert_called_once()

    # Verify environment was updated
    assert environ.last_message == mock_message
    assert environ.thread_id == "new-thread-id"


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_converse_with_last_message(mock_output, setup_assistant):
    # Setup environment with last message
    last_message = MagicMock()
    last_message.thread_id = "last-thread-id"

    environ = IoEnviron(
        assistant=setup_assistant,
        thread_id="thread-id",
        user_input="Hello AI",
        last_message=last_message,
    )

    # Call the function
    await converse(environ)

    # Verify assistant.converse was called with last_message.thread_id
    setup_assistant.converse.assert_called_once_with("Hello AI", "last-thread-id")


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_converse_no_response(mock_output, setup_assistant):
    # Setup assistant to return None
    setup_assistant.converse.return_value = None

    # Setup environment
    environ = IoEnviron(
        assistant=setup_assistant, thread_id="thread-id", user_input="Hello AI"
    )

    # Call the function
    await converse(environ)

    # Verify warning was displayed
    mock_output.warn.assert_called_once_with("No response from the AI model.")


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_converse_empty_response(mock_output, setup_assistant):
    # Setup assistant to return message with empty content
    message = MagicMock(spec=MessageData)
    message.text_content = ""
    setup_assistant.converse.return_value = message

    # Setup environment
    environ = IoEnviron(
        assistant=setup_assistant, thread_id="thread-id", user_input="Hello AI"
    )

    # Call the function
    await converse(environ)

    # Verify warning was displayed
    mock_output.warn.assert_called_once_with("No response from the AI model.")


@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_converse_duplicate_response(mock_output, setup_assistant, mock_message):
    # Setup last message with same content as new message
    last_message = MagicMock(spec=MessageData)
    last_message.text_content = "AI response"

    # Setup environment
    environ = IoEnviron(
        assistant=setup_assistant,
        thread_id="thread-id",
        user_input="Hello AI",
        last_message=last_message,
    )

    # Call the function
    await converse(environ)

    # Verify warning was displayed
    mock_output.warn.assert_called_once_with("No response from the AI model.")


@patch("assistants.cli.io_loop.highlight_code_blocks")
@patch("assistants.cli.io_loop.output")
@pytest.mark.asyncio
async def test_converse_with_code_blocks(
    mock_output, mock_highlight, setup_assistant, mock_message
):
    # Setup highlight to return formatted text
    mock_highlight.return_value = "formatted response"

    # Setup environment
    environ = IoEnviron(
        assistant=setup_assistant, thread_id="thread-id", user_input="Hello AI"
    )

    # Call the function
    await converse(environ)

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
