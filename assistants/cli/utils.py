import os
import re
import subprocess
import tempfile
from argparse import Namespace
from typing import Optional, cast

from pygments import highlight
from pygments.formatter import Formatter
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name

from assistants.ai.anthropic import Claude
from assistants.ai.openai import Assistant, Completion
from assistants.ai.types import AssistantProtocol
from assistants.cli import output
from assistants.config import environment
from assistants.lib.exceptions import ConfigError
from assistants.user_data.sqlite_backend.threads import (
    get_last_thread_for_assistant,
)


def highlight_code_blocks(markdown_text):
    code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

    def replacer(match):
        lang = match.group(1)
        code = match.group(2)
        if lang:
            if lang == "plaintext":
                lang = "text"
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
) -> tuple[AssistantProtocol, Optional[str]]:
    thread_id = None

    if args.code:
        if environment.CODE_MODEL.startswith("o1"):
            # Create a completion model for code reasoning (slower and more expensive)
            assistant = Completion(model=environment.CODE_MODEL)
        elif environment.CODE_MODEL.startswith("claude-"):
            # Create an Anthropic assistant for code reasoning
            assistant = Claude(model=environment.CODE_MODEL)
        else:
            raise ConfigError(f"Invalid code reasoning model: {environment.CODE_MODEL}")
        if args.continue_thread:
            await assistant.start()
        thread_id = assistant.conversation_id
    else:
        # Create a default assistant
        if args.instructions:
            try:
                with open(args.instructions, "r") as instructions_file:
                    instructions_text = instructions_file.read()
            except FileNotFoundError:
                raise ConfigError(f"Instructions file not found: '{args.instructions}'")
        else:
            instructions_text = environment.ASSISTANT_INSTRUCTIONS

        if environment.DEFAULT_MODEL.startswith("claude-"):
            # We can also use Claude as the default model
            assistant = Claude(model=environment.DEFAULT_MODEL)
            if args.continue_thread:
                await assistant.start()
                thread_id = assistant.conversation_id
            if instructions_text:
                output.warn(
                    "Custom instructions are currently not supported with this assistant."
                )
        else:
            assistant = Assistant(
                name=environment.ASSISTANT_NAME,
                model=environment.DEFAULT_MODEL,
                instructions=instructions_text,
                tools=[{"type": "code_interpreter"}],
            )
            await assistant.start()
            thread = await get_last_thread_for_assistant(assistant.assistant_id)
            thread_id = thread.thread_id if thread else None

    assistant = cast(AssistantProtocol, assistant)

    return assistant, thread_id
