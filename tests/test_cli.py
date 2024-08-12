import os
import random
import pytest
from unittest.mock import patch, MagicMock

from bot.cli import cli
from bot.exceptions import NoResponseError
from bot.helpers import get_text_from_default_editor


class MockText:
    value: str = "Hello!"


class MockContent:
    text: MockText = MockText()


class MockMessage:
    content = [MockContent()]

    def __init__(self, _id=None, thread_id=None):
        self.id = _id or self.random_id()
        self.thread_id = thread_id or self.random_id()

    @staticmethod
    def random_id():
        return str(random.randint(10000, 99999))


@pytest.mark.parametrize("exit_keyword", ["q", "Q", "quit", "QUIT", "Quit", "quiT"])
def test_exit_keywords_exit_the_program(exit_keyword):
    with patch(
        "bot.ai.assistant.Assistant.converse",
        return_value=MockMessage(thread_id="123"),
    ) as mock_converse:
        with patch("builtins.input", lambda *args: exit_keyword):
            cli()
        assert not mock_converse.called


@patch("builtins.input", lambda *args: "Hello!")
def test_conversation_does_not_get_stuck_in_loop_if_final_message_doesnt_change():
    with patch(
        "bot.ai.assistant.Assistant.converse",
        return_value=MockMessage(_id="1"),
    ) as mock_converse:
        with pytest.raises(NoResponseError):
            cli()
        assert mock_converse.call_count == 2


def test_get_text_from_default_editor(mocker):
    # Create a mock for the temporary file
    mock_temp_file = MagicMock()
    mock_temp_file.name = "tempfile.md"  # Simulate a valid temporary file name

    # Set up the NamedTemporaryFile mock
    mocker.patch("tempfile.NamedTemporaryFile", return_value=mock_temp_file)

    # Mock __enter__ to return the temp file itself
    mock_temp_file.__enter__.return_value = mock_temp_file

    # Mock open() to simulate reading from the file
    mock_open = mocker.patch(
        "builtins.open", mocker.mock_open(read_data="Hello from editor!")
    )

    # Mock subprocess.run to simulate running the editor
    mock_subprocess = mocker.patch("subprocess.run")

    # We can also mock os.remove to avoid FileNotFoundError during the test
    mock_remove = mocker.patch("os.remove")

    # Call the function under test
    result = get_text_from_default_editor()

    # Assert the expected result and that mocks were called correctly
    assert result == "Hello from editor!"
    mock_open.assert_called_once_with(
        mock_temp_file.name, "r"
    )  # Now this should succeed
    mock_subprocess.assert_called_once_with(
        [os.environ.get("EDITOR", "nano"), mock_temp_file.name]
    )  # Check subprocess call

    # Ensure __enter__ and __exit__ were called
    mock_temp_file.__enter__.assert_called_once()
    mock_temp_file.__exit__.assert_called_once()

    # Verify that os.remove was called with the correct file path.
    mock_remove.assert_called_once_with(mock_temp_file.name)
