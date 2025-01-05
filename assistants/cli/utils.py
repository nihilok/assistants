import os
import re
import subprocess
import tempfile
from argparse import Namespace
from typing import Optional

from pygments import highlight
from pygments.formatter import Formatter
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name

from assistants.ai.assistant import Assistant, Completion
from assistants.config import environment

from assistants.user_data.sqlite_backend.threads import (
    get_last_thread_for_assistant,
    ThreadData,
)


class GreyTextFormatter(Formatter):
    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            outfile.write(f"\033[90m{value}\033[0m")


def highlight_code_blocks(markdown_text):
    code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

    def replacer(match):
        lang = match.group(1)
        code = match.group(2)
        if lang:
            lexer = get_lexer_by_name(lang, stripall=True)
        else:
            lexer = get_lexer_by_name("text", stripall=True)
        return f"```{lang if lang else ''}\n{highlight(code, lexer, TerminalFormatter())}```"

    return code_block_pattern.sub(replacer, markdown_text)


async def get_thread_id(assistant_id: str):
    last_thread = await get_last_thread_for_assistant(assistant_id)
    return last_thread.thread_id if last_thread else None


def get_text_from_default_editor(initial_text=None):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
        temp_file_path = temp_file.name

    if initial_text:
        with open(temp_file_path, "w") as text_file:
            text_file.write(initial_text)

    # Open the editor for the user to input text
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, temp_file_path])

    # Read the contents of the file after the editor is closed
    with open(temp_file_path, "r") as file:
        text = file.read()

    # Remove the temporary file
    os.remove(temp_file_path)

    return text


async def create_assistant_and_thread(
    args: Namespace,
) -> tuple[Assistant, Optional[ThreadData]]:
    if args.code:
        # Create a completion model for code reasoning (slower and more expensive)
        assistant = Completion(model=environment.CODE_MODEL)
        thread = None  # Threads are not supported with code reasoning
    else:
        # Create a default assistant
        assistant = Assistant(
            name="AI Assistant",
            model=environment.DEFAULT_MODEL,
            instructions=args.instructions or environment.ASSISTANT_INSTRUCTIONS,
            tools=[{"type": "code_interpreter"}],
        )
        await assistant.start()
        thread = await get_last_thread_for_assistant(assistant.assistant_id)

    return assistant, thread
