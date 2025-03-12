from unittest.mock import MagicMock, patch

import pytest

from assistants.cli.cli import cli
from assistants.lib.exceptions import ConfigError


@pytest.fixture(autouse=True)
def mock_select():
    with patch("assistants.cli.cli.select") as mock_select:
        mock_select.select.return_value = ([], [], [])
        yield mock_select


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=False,
        input_file=False,
        code=False,
        continue_thread=False,
        config_file=None,
        thinking=0,
    ),
)
@patch(
    "assistants.cli.cli.create_assistant_and_thread", return_value=(MagicMock(), None)
)
@patch("assistants.cli.cli.output")
def test_cli_runs_successfully(
    mock_output, mock_create_assistant_and_thread, mock_get_args
):
    with patch("assistants.cli.cli.io_loop") as mock_io_loop:
        cli()
        mock_io_loop.assert_called_once()


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=False,
        input_file=False,
        code=False,
        continue_thread=False,
        config_file=None,
        thinking=0,
    ),
)
@patch(
    "assistants.cli.cli.create_assistant_and_thread",
    side_effect=ConfigError("Invalid configuration"),
)
@patch("assistants.cli.cli.output")
def test_cli_exits_on_config_error(
    mock_output, mock_create_assistant_and_thread, mock_get_args
):
    with pytest.raises(SystemExit):
        cli()
    mock_output.fail.assert_called_once_with("Error: Invalid configuration")


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=False,
        input_file=None,
        code=False,
        continue_thread=False,
        config_file="nonexistent_file.txt",
        thinking=0,
    ),
)
@patch("assistants.cli.cli.output")
def test_cli_exits_on_config_file_not_found(mock_output, mock_get_args):
    with pytest.raises(SystemExit):
        cli()
    mock_output.fail.assert_called_once_with(
        "Error: The file 'nonexistent_file.txt' was not found."
    )


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=False,
        input_file=None,
        code=False,
        continue_thread=False,
        config_file=None,
        thinking=-1,
        model="dummy-model",
    ),
)
@patch("assistants.cli.cli.output")
def test_cli_exits_on_thinking_less_than_0(mock_output, mock_get_args):
    with pytest.raises(SystemExit):
        cli()
    mock_output.fail.assert_called_once_with(
        "Error: The 'thinking' level must be between 0 and 2."
    )


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=False,
        input_file=None,
        code=False,
        continue_thread=False,
        config_file=None,
        thinking=3,
        model="dummy-model",
    ),
)
@patch("assistants.cli.cli.output")
def test_cli_exits_on_thinking_more_than_2(mock_output, mock_get_args):
    with pytest.raises(SystemExit):
        cli()
    mock_output.fail.assert_called_once_with(
        "Error: The 'thinking' level must be between 0 and 2."
    )


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=False,
        input_file="nonexistent_file.txt",
        code=False,
        continue_thread=False,
        config_file=None,
        thinking=0,
    ),
)
@patch("assistants.cli.cli.output")
def test_cli_exits_on_file_not_found(mock_output, mock_get_args):
    with pytest.raises(SystemExit):
        cli()
    mock_output.fail.assert_called_once_with(
        "Error: The file 'nonexistent_file.txt' was not found."
    )


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=True,
        input_file=False,
        code=False,
        continue_thread=False,
        config_file=None,
        thinking=0,
    ),
)
@patch("assistants.cli.cli.get_text_from_default_editor", return_value="Edited text")
@patch(
    "assistants.cli.cli.create_assistant_and_thread", return_value=(MagicMock(), None)
)
@patch("assistants.cli.cli.output")
def test_cli_opens_editor(
    mock_output,
    mock_create_assistant_and_thread,
    mock_get_text_from_default_editor,
    mock_get_args,
):
    with patch("assistants.cli.cli.io_loop") as mock_io_loop:
        cli()
        mock_get_text_from_default_editor.assert_called_once()
        mock_io_loop.assert_called_once()


@patch(
    "assistants.cli.cli.get_args",
    return_value=MagicMock(
        prompt=None,
        editor=False,
        input_file=False,
        code=False,
        continue_thread=True,
        config_file=None,
        thinking=0,
    ),
)
@patch(
    "assistants.cli.cli.create_assistant_and_thread",
    return_value=(MagicMock(), MagicMock(thread_id="12345")),
)
@patch("assistants.cli.cli.output")
def test_cli_continues_thread(
    mock_output, mock_create_assistant_and_thread, mock_get_args
):
    with patch("assistants.cli.cli.io_loop") as mock_io_loop:
        cli()
        mock_io_loop.assert_called_once_with(
            mock_create_assistant_and_thread.return_value[0],
            None,
            thread_id=mock_create_assistant_and_thread.return_value[1],
        )
