import os
from unittest.mock import MagicMock

from assistants.cli.utils import get_text_from_default_editor


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
