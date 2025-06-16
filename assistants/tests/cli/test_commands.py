import asyncio
from unittest.mock import MagicMock, patch

import pyperclip  # type: ignore[import-untyped]

from assistants.cli.commands import CopyCodeBlocks, CopyResponse, IoEnviron


@patch("assistants.cli.commands.pyperclip.copy")
@patch("assistants.cli.commands.output.inform")
def test_copies_response_to_clipboard(mock_inform, mock_copy):
    environ = IoEnviron(
        assistant=MagicMock(), last_message=MagicMock(text_content="Response text")
    )
    command = CopyResponse()
    asyncio.run(command(environ))
    mock_copy.assert_called_once_with("Response text")
    mock_inform.assert_called_once_with("Copied response to clipboard")


@patch(
    "assistants.cli.commands.pyperclip.copy", side_effect=pyperclip.PyperclipException
)
@patch("assistants.cli.commands.output.fail")
def test_handles_clipboard_copy_error(mock_fail, mock_copy):
    environ = IoEnviron(
        assistant=MagicMock(), last_message=MagicMock(text_content="Response text")
    )
    command = CopyResponse()
    asyncio.run(command(environ))
    mock_fail.assert_called_once_with(
        "Error copying to clipboard; this feature doesn't seem to be available in the current terminal environment."
    )


@patch("assistants.cli.commands.output.warn")
def test_warns_when_no_previous_message_to_copy(mock_warn):
    environ = IoEnviron(assistant=MagicMock(), last_message=None)
    command = CopyResponse()
    asyncio.run(command(environ))
    mock_warn.assert_called_once_with("No previous message to copy.")


@patch("assistants.cli.commands.pyperclip.copy")
@patch("assistants.cli.commands.output.inform")
def test_copies_code_blocks_to_clipboard_with_lang_and_single_newline(
    mock_inform, mock_copy
):
    environ = IoEnviron(
        assistant=MagicMock(),
        last_message=MagicMock(text_content="```lang\ncode block```"),
    )
    command = CopyCodeBlocks()
    asyncio.run(command(environ))
    mock_copy.assert_called_once_with("code block")
    mock_inform.assert_called_once_with("Copied code block to clipboard")


@patch("assistants.cli.commands.pyperclip.copy")
@patch("assistants.cli.commands.output.inform")
def test_copies_code_blocks_to_clipboard_with_lang_and_newlines(mock_inform, mock_copy):
    environ = IoEnviron(
        assistant=MagicMock(),
        last_message=MagicMock(text_content="```lang\ncode block\n```"),
    )
    command = CopyCodeBlocks()
    asyncio.run(command(environ))
    mock_copy.assert_called_once_with("code block")
    mock_inform.assert_called_once_with("Copied code block to clipboard")


@patch("assistants.cli.commands.pyperclip.copy")
@patch("assistants.cli.commands.output.inform")
def test_copies_code_blocks_to_clipboard_with_newline_only(mock_inform, mock_copy):
    environ = IoEnviron(
        assistant=MagicMock(), last_message=MagicMock(text_content="```\ncode block```")
    )
    command = CopyCodeBlocks()
    asyncio.run(command(environ))
    mock_copy.assert_called_once_with("code block")
    mock_inform.assert_called_once_with("Copied code block to clipboard")


@patch("assistants.cli.commands.pyperclip.copy")
@patch("assistants.cli.commands.output.inform")
def test_copies_code_blocks_without_newlines_to_clipboard(mock_inform, mock_copy):
    environ = IoEnviron(
        assistant=MagicMock(), last_message=MagicMock(text_content="```code block```")
    )
    command = CopyCodeBlocks()
    asyncio.run(command(environ))
    mock_copy.assert_called_once_with("code block")
    mock_inform.assert_called_once_with("Copied code block to clipboard")


@patch("assistants.cli.commands.pyperclip.copy")
@patch("assistants.cli.commands.output.inform")
def test_copies_multiple_code_blocks_to_clipboard(mock_inform, mock_copy):
    environ = IoEnviron(
        assistant=MagicMock(),
        last_message=MagicMock(
            text_content="```code block```\n```\ncode block 2\n```\n\nsomething else\n```python\ncode block 3```"
        ),
    )
    command = CopyCodeBlocks()
    asyncio.run(command(environ))
    mock_copy.assert_called_once_with("code block\n\ncode block 2\n\ncode block 3")
    mock_inform.assert_called_once_with("Copied code blocks to clipboard")


@patch("assistants.cli.commands.pyperclip.copy")
@patch("assistants.cli.commands.output.inform")
def test_copies_image_url_to_clipboard(mock_inform, mock_copy):
    environ = IoEnviron(
        assistant=MagicMock(),
        last_message=MagicMock(text_content="https://example.com/image.png"),
    )
    command = CopyResponse()
    asyncio.run(command(environ))
    mock_copy.assert_called_once_with("https://example.com/image.png")
    mock_inform.assert_called_once_with("Copied image URL to clipboard")


@patch("assistants.cli.commands.output.warn")
def test_warns_when_no_code_blocks_to_copy(mock_warn):
    environ = IoEnviron(
        assistant=MagicMock(),
        last_message=MagicMock(text_content="No code blocks here"),
    )
    command = CopyCodeBlocks()
    asyncio.run(command(environ))
    mock_warn.assert_called_once_with("No codeblocks in previous message!")
