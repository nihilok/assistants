import asyncio
import re
from dataclasses import dataclass
from typing import Protocol, Optional

import pyperclip
from openai.types.beta.threads import Message

from assistants.ai.assistant import Completion, AssistantProtocol
from assistants.cli import output
from assistants.cli.constants import IO_INSTRUCTIONS
from assistants.cli.selector import TerminalSelector
from assistants.cli.terminal import clear_screen
from assistants.cli.utils import get_text_from_default_editor
from assistants.user_data import threads_table


@dataclass
class IoEnviron:
    """
    Environment variables for the input/output loop.
    """

    assistant: AssistantProtocol
    last_message: Optional[Message] = None
    thread_id: Optional[str] = None


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
            return

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
        asyncio.run(environ.assistant.start())
        clear_screen()


new_thread: Command = NewThread()


class SelectThread(Command):
    """
    Command to select a thread.
    """

    def __call__(self, environ: IoEnviron) -> None:
        """
        Call the command to select a thread.

        :param environ: The environment variables for the input/output loop.
        """
        threads = asyncio.run(
            threads_table.get_by_assistant_id(environ.assistant.assistant_id)
        )
        if not threads:
            output.warn("No threads found.")
            return

        threads_output = [
            f"{thread.last_run_dt} | {thread.thread_id} | {thread.initial_prompt}"
            for i, thread in enumerate(threads)
        ]
        selector = TerminalSelector(threads_output)
        result = selector.run()
        if not result:
            output.warn("No thread selected.")
            return
        thread_id = result.split("|")[1].strip()
        environ.thread_id = thread_id
        environ.last_message = None
        asyncio.run(environ.assistant.start())


select_thread: Command = SelectThread()


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
    "/t": select_thread,
    "/threads": select_thread,
}
