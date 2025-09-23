import asyncio
import io
import sys
from unittest import mock

import pytest
from unittest.mock import MagicMock, patch, mock_open, Mock, AsyncMock

import yaml

from assistants.cli.cli import CLI
from assistants.lib.exceptions import ConfigError


@pytest.fixture
def cli():
    return CLI()


@patch("setproctitle.setproctitle")
def test_set_process_title(mock_setproctitle, cli):
    cli.set_process_title()
    mock_setproctitle.assert_called_once_with("assistant-cli")


@patch("sys.argv", ["test"])
@patch("assistants.cli.cli.get_args")
def test_parse_arguments(mock_get_args, cli):
    mock_args = MagicMock()
    mock_get_args.return_value = mock_args

    cli.parse_arguments()

    mock_get_args.assert_called_once()
    assert cli.args == mock_args


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open, read_data="config_data")
@patch("assistants.cli.cli.environment")
@patch("assistants.cli.cli.update_args_from_config_file")
def test_update_from_config_success(
    mock_update_args, mock_env, mock_file, mock_yaml_load, cli
):
    mock_config = {"key": "value"}
    mock_yaml_load.return_value = mock_config

    cli.args = MagicMock()
    cli.args.config_file = "config.yaml"

    cli.update_from_config()

    mock_file.assert_called_once_with("config.yaml")
    mock_yaml_load.assert_called_once_with(mock_file())
    mock_env.update_from_config_yaml.assert_called_once_with(mock_config)
    mock_update_args.assert_called_once_with(mock_config, cli.args)


@patch("assistants.cli.output.fail")
@patch("sys.exit")
@patch("builtins.open", side_effect=FileNotFoundError)
def test_update_from_config_file_not_found(mock_open, mock_exit, mock_fail, cli):
    cli.args = MagicMock()
    cli.args.config_file = "nonexistent.yaml"

    cli.update_from_config()

    mock_fail.assert_called_once_with(
        "Error: The file 'nonexistent.yaml' was not found."
    )
    mock_exit.assert_called_once_with(1)


@patch("assistants.cli.output.fail")
@patch("sys.exit")
@patch("yaml.safe_load", side_effect=yaml.YAMLError("YAML error"))
@patch("builtins.open", new_callable=mock_open, read_data="invalid yaml")
def test_update_from_config_yaml_error(
    mock_file, mock_yaml_load, mock_exit, mock_fail, cli
):
    cli.args = MagicMock()
    cli.args.config_file = "invalid.yaml"

    cli.update_from_config()

    mock_fail.assert_called_once_with("Error: YAML error")
    mock_exit.assert_called_once_with(1)


@patch("assistants.cli.output.fail")
@patch("sys.exit")
@patch("assistants.config.environment")
def test_validate_arguments_invalid_thinking(mock_env, mock_exit, mock_fail, cli):
    cli.args = MagicMock()
    cli.args.thinking = 3  # Invalid value

    cli.validate_arguments()

    mock_fail.assert_called_once_with(
        "Error: The 'thinking' level must be between 0 and 2."
    )
    mock_exit.assert_called_once_with(1)


@patch("assistants.cli.cli.environment")
def test_validate_arguments_default_model(mock_env, cli):
    cli.args = MagicMock()
    cli.args.thinking = 1
    cli.args.model = None
    cli.args.legacy = True

    mock_env.DEFAULT_MODEL = "default-model"
    cli.validate_arguments()
    assert cli.args.model == "default-model"


@patch("select.select")
def test_prepare_initial_input_from_stdin(mock_select, cli):
    mock_select.return_value = ([sys.stdin], [], [])

    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = "stdin input"
        cli.args = MagicMock()
        cli.args.prompt = None
        cli.args.editor = False
        cli.args.input_file = None

        cli.prepare_initial_input()

        assert cli.args.prompt == ["stdin", "input"]


@patch("subprocess.run")
@patch("assistants.cli.cli.get_text_from_default_editor")
def test_prepare_initial_input_editor_mode(mock_get_text, mock_subprocess, cli):
    mock_get_text.return_value = "edited text"

    cli.args = MagicMock()
    cli.args.prompt = ["initial", "prompt"]
    cli.args.editor = True

    cli.prepare_initial_input()

    mock_get_text.assert_called_once_with("initial prompt")
    assert cli.initial_input == "edited text"


@patch("builtins.open", new_callable=mock_open, read_data="file content")
def test_prepare_initial_input_from_file(mock_file, cli):
    cli.args = MagicMock()
    cli.args.prompt = None
    cli.args.editor = False
    cli.args.input_file = "input.txt"

    cli.prepare_initial_input()

    mock_file.assert_called_once_with("input.txt", "r", encoding="utf-8")
    assert cli.initial_input == "file content"


@patch("assistants.cli.output.fail")
@patch("sys.exit")
@patch("builtins.open", side_effect=FileNotFoundError)
def test_prepare_initial_input_file_not_found(mock_open, mock_exit, mock_fail, cli):
    cli.args = MagicMock()
    cli.args.prompt = None
    cli.args.editor = False
    cli.args.input_file = "nonexistent.txt"

    cli.prepare_initial_input()

    mock_fail.assert_called_once_with(
        "Error: The file 'nonexistent.txt' was not found."
    )
    mock_exit.assert_called_once_with(1)


def test_prepare_initial_input_from_prompt(cli):
    cli.args = MagicMock()
    cli.args.prompt = ["hello", "world"]
    cli.args.editor = False
    cli.args.input_file = None

    cli.prepare_initial_input()

    assert cli.initial_input == "hello world"


@patch("assistants.cli.cli.display_welcome_message")
def test_show_welcome_message(mock_display, cli):
    cli.args = MagicMock()

    cli.show_welcome_message()

    mock_display.assert_called_once_with(cli.args)


@patch("assistants.cli.cli.create_assistant_and_thread")
def test_create_assistant(mock_create, cli):
    expected_result = (MagicMock(), "thread-id")
    mock_create.return_value = expected_result
    cli.args = MagicMock()
    cli.args.thinking = 1  # Set a proper integer value

    result = asyncio.run(cli.create_assistant())

    mock_create.assert_called_once_with(cli.args, mock.ANY)
    assert result == expected_result


@patch("assistants.cli.output.warn")
def test_handle_conversation_status_no_thread_with_continue(mock_warn, cli):
    cli.thread_id = None
    cli.args = MagicMock()
    cli.args.continue_thread = True

    asyncio.run(cli.handle_conversation_status())

    mock_warn.assert_called_once_with(
        "Warning: could not read last thread id; starting new thread."
    )


@patch("assistants.cli.output.inform")
@patch("assistants.cli.output.new_line")
@patch("assistants.cli.cli.display_conversation_history")
def test_handle_conversation_status_with_thread_and_continue(mock_display, mock_new_line, mock_inform, cli):
    cli.thread_id = "thread-id"
    cli.assistant = MagicMock()
    cli.args = MagicMock()
    cli.args.continue_thread = True

    # Mock display_conversation_history as an async function using AsyncMock
    async def mock_async_display(*args, **kwargs):
        return None

    mock_display.side_effect = mock_async_display

    asyncio.run(cli.handle_conversation_status())

    mock_inform.assert_called_once_with("Continuing previous thread...")
    mock_new_line.assert_called_once()
    mock_display.assert_called_once_with(cli.assistant, "thread-id")


@patch("assistants.cli.cli.io_loop")
def test_start_io_loop(mock_io_loop, cli):
    cli.assistant = MagicMock()
    cli.initial_input = "initial input"
    cli.thread_id = "thread-id"

    cli.start_io_loop()

    mock_io_loop.assert_called_once_with(
        cli.assistant, "initial input", thread_id="thread-id"
    )


@patch("assistants.cli.cli.io_loop", side_effect=KeyboardInterrupt)
@patch("sys.exit")
def test_start_io_loop_keyboard_interrupt(mock_exit, mock_io_loop, cli):
    cli.assistant = MagicMock()

    cli.start_io_loop()

    mock_exit.assert_called_once_with(0)


@patch.object(CLI, "set_process_title")
@patch.object(CLI, "parse_arguments")
@patch.object(CLI, "update_from_config")
@patch.object(CLI, "validate_arguments")
@patch.object(CLI, "prepare_initial_input")
@patch.object(CLI, "show_welcome_message")
@patch.object(CLI, "handle_conversation_status")
@patch.object(CLI, "start_io_loop")
@patch("asyncio.run")
def test_run_success(
    mock_asyncio_run,
    mock_start_io,
    mock_handle_conv,
    mock_welcome,
    mock_prepare,
    mock_validate,
    mock_update,
    mock_parse,
    mock_set_title,
    cli,
):
    mock_assistant = MagicMock()
    mock_thread_id = "thread-id"
    mock_asyncio_run.return_value = (mock_assistant, mock_thread_id)

    cli.run()

    mock_set_title.assert_called_once()
    mock_parse.assert_called_once()
    mock_update.assert_called_once()
    mock_validate.assert_called_once()
    mock_prepare.assert_called_once()
    mock_welcome.assert_called_once()
    mock_handle_conv.assert_called_once()
    mock_start_io.assert_called_once()
    assert cli.assistant == mock_assistant
    assert cli.thread_id == mock_thread_id


@patch.object(CLI, "handle_conversation_status")
@patch.object(CLI, "start_io_loop")
@patch.object(CLI, "set_process_title")
@patch.object(CLI, "parse_arguments")
@patch.object(CLI, "update_from_config")
@patch.object(CLI, "validate_arguments")
@patch.object(CLI, "prepare_initial_input")
@patch.object(CLI, "show_welcome_message")
@patch.object(CLI, "create_assistant")
@patch("assistants.cli.output.fail")
@patch("sys.exit")
def test_run_config_error(
    mock_exit,
    mock_fail,
    mock_create_assistant,
    mock_welcome,
    mock_prepare,
    mock_validate,
    mock_update,
    mock_parse,
    mock_set_title,
    mock_start_io,
    mock_handle_conv,
    cli,
):
    # Mock all methods to prevent any other sys.exit calls
    mock_parse.return_value = None
    mock_update.return_value = None
    mock_validate.return_value = None
    mock_prepare.return_value = None
    mock_welcome.return_value = None
    mock_create_assistant.side_effect = ConfigError("Config error")

    cli.run()

    mock_fail.assert_called_once_with("Error: Config error")
    mock_exit.assert_called_once_with(1)
