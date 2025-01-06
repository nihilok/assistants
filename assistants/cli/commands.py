import re
from typing import Protocol

import pyperclip

from assistants.ai.assistant import Completion
from assistants.cli import output
from assistants.cli.constants import IO_INSTRUCTIONS
from assistants.cli.io_loop import IoEnviron
from assistants.cli.terminal import clear_screen
from assistants.cli.utils import get_text_from_default_editor


class Command(Protocol):
    """
    Command protocol for the input/output loop.
    """

    def __call__(self, environ: IoEnviron) -> None:
        """
        Call the command.

        :param environ: The environment variables for the input/output loop.
        """
        ...


class Editor(Command):
    """
    Command to open the default text editor.
    """

    def __call__(self, environ: IoEnviron) -> None:
        """
        Call the command to open the default text editor.

        :param environ: The environment variables for the input/output loop.
        """
        environ.user_input = get_text_from_default_editor().strip()
        output.user_input(environ.user_input)


editor: Command = Editor()


class CopyResponse(Command):
    """
    Command to copy the response to the clipboard.
    """

    @staticmethod
    def copy_to_clipboard(text: str) -> None:
        """
        Copy the given text to the clipboard.

        :param text: The text to copy to the clipboard.
        """
        try:
            pyperclip.copy(text)
        except pyperclip.PyperclipException:
            output.fail(
                "Error copying to clipboard; this feature doesn't seem to be "
                "available in the current terminal environment."
            )
            return

    def get_previous_response(self, environ: IoEnviron) -> str:
        """
        Get the previous response from the assistant.

        :param environ: The environment variables for the input/output loop.
        :return: The previous response from the assistant.
        """
        assistant = environ.assistant
        previous_response = ""
        if isinstance(assistant, Completion):
            if assistant.memory:
                previous_response = assistant.memory[-1]["content"]  # type: ignore

        elif environ.last_message:
            previous_response = last_message.content[0].text.value  # type: ignore

        return previous_response

    def __call__(self, environ: IoEnviron) -> None:
        """
        Call the command to copy the response to the clipboard.

        :param environ: The environment variables for the input/output loop.
        """
        previous_response = self.get_previous_response(environ)

        if not previous_response:
            output.warn("No previous message to copy.")
            return

        self.copy_to_clipboard(previous_response)
        output.inform("Copied response to clipboard")


copy_response: Command = CopyResponse()


class CopyCodeBlocks(CopyResponse):
    """
    Command to copy the code blocks from the response to the clipboard.
    """

    def __call__(self, environ: IoEnviron) -> None:
        """
        Call the command to copy the code blocks from the response to the clipboard.

        :param environ: The environment variables for the input/output loop.
        """
        previous_response = self.get_previous_response(environ)

        if not previous_response:
            output.warn("No previous message to copy from.")
            return

        code_blocks = re.split(r"(```.*?```)", previous_response, flags=re.DOTALL)

        code_only = [
            "\n".join(block.split("\n")[1:-1]).strip()
            for block in code_blocks
            if block.startswith("```")
        ]

        if not code_only:
            output.warn("No codeblocks in previous message!")
            continue

        all_code = "\n\n".join(code_only)

        self.copy_to_clipboard(all_code)

        output.inform("Copied code blocks to clipboard")


copy_code_blocks: Command = CopyCodeBlocks()


class PrintUsage(Command):
    """
    Command to print the usage instructions.
    """

    def __call__(self, environ: IoEnviron) -> None:
        """
        Call the command to print the usage instructions.

        :param environ: The environment variables for the input/output loop.
        """
        output.inform(IO_INSTRUCTIONS)


print_usage: Command = PrintUsage()


class NewThread(Command):
    """
    Command to start a new thread.
    """

    def __call__(self, environ: IoEnviron) -> None:
        """
        Call the command to start a new thread.

        :param environ: The environment variables for the input/output loop.
        """
        environ.thread_id = None
        environ.last_message = None
        clear_screen()


new_thread: Command = NewThread()


COMMAND_MAP = {
    "/e": editor,
    "/edit": editor,
    "/editor": editor,
    "/c": copy_response,
    "/copy": copy_response,
    "/cc": copy_code_blocks,
    "/copy-code": copy_code_blocks,
    "/h": print_usage,
    "/help": print_usage,
    "help": print_usage,
    "/n": new_thread,
    "/new": new_thread,
    "/new-thread": new_thread,
}
