import json
import re
import webbrowser
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

import aiofiles
import aiohttp
import pyperclip

from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.openai import Assistant
from assistants.ai.types import MessageData, AssistantInterface
from assistants.cli import output
from assistants.lib.constants import IO_INSTRUCTIONS
from assistants.cli.selector import TerminalSelector, TerminalSelectorOption
from assistants.cli.terminal import clear_screen
from assistants.cli.utils import get_text_from_default_editor, highlight_code_blocks
from assistants.config import environment
from assistants.config.file_management import DATA_DIR
from assistants.user_data.sqlite_backend import conversations_table
from assistants.user_data.sqlite_backend.conversations import Conversation


@dataclass
class IoEnviron:
    """
    Environment variables for the input/output loop.
    """

    assistant: AssistantInterface
    last_message: Optional[MessageData] = None
    thread_id: Optional[str] = None
    user_input: Optional[str] = None


class Command(ABC):
    """
    Command protocol for the input/output loop.
    """

    @abstractmethod
    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command.

        :param environ: The environment variables for the input/output loop.
        """

    @property
    @abstractmethod
    def help(self) -> str:
        """
        Get the help text for the command.

        :return: The help text for the command.
        """


class Editor(Command):
    """
    Command to open the default text editor.
    """

    help = "Open the default text editor to compose a prompt"

    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command to open the default text editor.

        :param environ: The environment variables for the input/output loop.
        """
        environ.user_input = get_text_from_default_editor().strip()


editor: Command = Editor()


class CopyResponse(Command):
    """
    Command to copy the response to the clipboard.
    """

    help = "Copy the last response to the clipboard"

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

    @staticmethod
    def get_previous_response(environ: IoEnviron) -> str:
        """
        Get the previous response from the assistant.

        :param environ: The environment variables for the input/output loop.
        :return: The previous response from the assistant.
        """
        previous_response = ""

        if environ.last_message:
            previous_response = environ.last_message.text_content

        return previous_response

    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command to copy the response to the clipboard.

        :param environ: The environment variables for the input/output loop.
        """
        previous_response = self.get_previous_response(environ)

        if not previous_response:
            output.warn("No previous message to copy.")
            return

        # Check if previous response is a URL
        if re.match(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            previous_response,
        ):
            message = "image URL"
        else:
            message = "response"

        self.copy_to_clipboard(previous_response)
        output.inform(f"Copied {message} to clipboard")


copy_response: Command = CopyResponse()


class CopyCodeBlocks(CopyResponse):
    """
    Command to copy the code blocks from the response to the clipboard.
    """

    help = (
        "Copy code blocks from the last response to the clipboard; optionally specify an index "
        "to copy a specific code block"
    )

    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command to copy the code blocks from the response to the clipboard.

        :param environ: The environment variables for the input/output loop.
        """
        previous_response = self.get_previous_response(environ)

        if not previous_response:
            output.warn("No previous message to copy from.")
            return

        split_code = re.split(r"(```.*?```)", previous_response, flags=re.DOTALL)

        pattern = r"```(?:[a-zA-Z]+(\n))?(\n)?([\s\S]*?)\n?```"
        replacement = r"\1\2\3\2\1"

        code_blocks = [
            re.sub(pattern, replacement, block)
            for block in split_code
            if block.startswith("```")
        ]

        if args:
            try:
                code_blocks = [code_blocks[int(str(args[0]))]]
            except (ValueError, IndexError):
                output.fail(
                    "Pass the index of the code block to copy, or no arguments to copy all code blocks."
                )
                return

        if not code_blocks:
            output.warn("No codeblocks in previous message!")
            return

        if code_blocks[0].startswith("\n"):
            code_blocks[0] = code_blocks[0][1:]  # Remove the leading newline
        if code_blocks[-1].endswith("\n"):
            code_blocks[-1] = code_blocks[-1][:-1]  # Remove the trailing newline

        if len(code_blocks) > 1:
            for i, block in enumerate(code_blocks[:-1]):
                if not block.endswith("\n"):
                    code_blocks[i] = block + "\n"

        all_code = "".join(code_blocks)

        self.copy_to_clipboard(all_code)

        output.inform(
            f"Copied code block{'s' if not args and len(code_blocks) > 1 else ''} to clipboard"
        )


copy_code_blocks: Command = CopyCodeBlocks()


class PrintUsage(Command):
    """
    Command to print the usage instructions.
    """

    help = "Print the usage instructions"

    async def __call__(self, environ: IoEnviron, *args) -> None:
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

    help = "Start a new thread and clear the screen"

    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command to start a new thread.

        :param environ: The environment variables for the input/output loop.
        """
        environ.thread_id = None
        environ.last_message = None
        await environ.assistant.start()
        clear_screen()


new_thread: Command = NewThread()


class SelectThread(Command):
    """
    Command to select a thread.
    """

    help = "Select a previous thread to load/continue"

    @staticmethod
    def get_first_prompt(thread: Conversation) -> str:
        """
        Get the first prompt from the thread.

        :param thread: The thread to get the first prompt from.
        :return: The first prompt from the thread.
        """
        conversation = json.loads(thread.conversation)
        if not conversation:
            return ""
        return next((p["content"] for p in conversation if p["role"] == "user"), "")

    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command to select a thread.

        :param environ: The environment variables for the input/output loop.
        """
        if isinstance(environ.assistant, ConversationHistoryMixin):
            threads = await conversations_table.get_all_conversations()
            thread_options = [
                TerminalSelectorOption(
                    label=f"{thread.last_updated} | {self.get_first_prompt(thread)}",
                    value=thread.id,
                )
                for thread in threads
            ]
        else:
            raise ValueError("Unsupported Interface")

        if not threads:
            output.warn("No threads found.")
            return

        selector = TerminalSelector(
            thread_options, title="Select a thread to continue..."
        )
        thread_id = selector.run()
        if not thread_id:
            return  # No change

        if thread_id == environ.thread_id:
            return  # No change

        environ.thread_id = thread_id

        if isinstance(environ.assistant, ConversationHistoryMixin):
            await environ.assistant.load_conversation(thread_id)
        else:
            await environ.assistant.start()

        output.inform(f"Selected thread '{thread_id}'")

        last_message = await environ.assistant.get_last_message(thread_id)
        environ.last_message = last_message

        if last_message:
            output.default(highlight_code_blocks(last_message.text_content))
            output.new_line(2)
        else:
            output.warn("No last message found in thread")


select_thread: Command = SelectThread()


class GenerateImage(Command):
    """
    Command to generate an image from a prompt.
    """

    help = "Generate an image from a prompt"

    @staticmethod
    async def save_image(image_url: str, prompt: str) -> None:
        """
        Save the image URL to the database.

        :param image_url: The URL of the image to save.
        :param prompt: The prompt that was used to create the image.
        """
        # Get the image content
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                image_content = await response.read()

        # Save the image to file
        image_path = DATA_DIR / "images"
        if not image_path.exists():
            image_path.mkdir(parents=True)

        filename = f"{'_'.join(prompt.split())}_{datetime.now(UTC).timestamp()}.png"
        image_path /= filename

        async with aiofiles.open(image_path, "wb") as file:
            await file.write(image_content)

        output.inform(f"Image saved to {image_path}")

    async def __call__(self, environ: IoEnviron, *args) -> None:
        assistant = environ.assistant
        if not isinstance(assistant, Assistant):
            raise NotImplementedError

        prompt = " ".join(args)

        image_url = await assistant.image_prompt(prompt)

        if image_url:
            output.default(f"Here's your image:\n{image_url}")
            output.new_line(2)

            environ.last_message = MessageData(
                text_content=image_url, thread_id=environ.thread_id
            )

            if environment.OPEN_IMAGES_IN_BROWSER:
                webbrowser.open(image_url)
                output.inform("Opening image in browser...")

            if input("Would you like to save this image? (y/N): ").lower() == "y":
                await self.save_image(image_url, prompt)

        else:
            output.warn("No image returned...")


generate_image: Command = GenerateImage()


class ShowLastMessage(Command):
    """
    Command to show the last message in the current thread.
    """

    help = "Show the last message in the current thread"

    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command to show the last message in the current thread.
        """
        if not environ.thread_id:
            output.warn("No thread selected.")
            return
        last_message = await environ.assistant.get_last_message(environ.thread_id)
        if last_message:
            output.output(last_message.text_content)
        else:
            output.warn("No last message found.")


show_last_message: Command = ShowLastMessage()


class CopyEntireThread(Command):
    """
    Command to copy the entire thread to the clipboard.
    """

    help = "Copy the entire thread to the clipboard"

    async def __call__(self, environ: IoEnviron, *args) -> None:
        """
        Call the command to copy the entire thread to the clipboard.
        """
        if not environ.thread_id or not environ.last_message:
            output.warn("No thread selected.")
            return
        history = await environ.assistant.get_whole_thread()
        history_text = ""
        for message in history:
            if message["role"] == "user":
                history_text += f"User:\n{message['content']}\n\n"
            else:
                history_text += f"Assistant:\n{message['content']}\n\n"

        pyperclip.copy(history_text)
        output.inform("Copied thread to clipboard")


copy_thread = CopyEntireThread()


COMMAND_MAP = {
    "/e": editor,
    "/edit": editor,
    "/editor": editor,
    "/c": copy_response,
    "/copy": copy_response,
    "/cc": copy_code_blocks,
    "/copy-code": copy_code_blocks,
    "/ct": copy_thread,
    "/copy-thread": copy_thread,
    "/h": print_usage,
    "/help": print_usage,
    "/n": new_thread,
    "/new": new_thread,
    "/new-thread": new_thread,
    "/t": select_thread,
    "/threads": select_thread,
    "/i": generate_image,
    "/image": generate_image,
    "/last": show_last_message,
    "/l": show_last_message,
}

EXIT_COMMANDS = {
    "q",
    "quit",
    "exit",
    "/q",
    "/quit",
    "/exit",
}


def generate_help_text() -> str:
    """
    Generate the help text for the commands.

    :return: The help text for the commands with commands sharing the same help grouped together.
    """
    # Group commands by their help text
    help_to_commands = {}
    for command, cmd in COMMAND_MAP.items():
        if cmd.help in help_to_commands:
            help_to_commands[cmd.help].append(command)
        else:
            help_to_commands[cmd.help] = [command]

    # Format each entry with grouped commands
    formatted_lines = []
    for help_text, commands in help_to_commands.items():
        # Sort commands to group aliases together
        commands.sort(key=len)  # Sort by length to put short commands first
        command_group = ", ".join(commands)
        formatted_lines.append(f"{command_group}: {help_text}")

    return (
        "\n".join(formatted_lines)
        + "\nCTRL+L to clear the screen\nCTRL+C or CTRL+D to exit"
    )


if __name__ == "__main__":
    print(generate_help_text())
