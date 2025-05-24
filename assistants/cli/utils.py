import os
import re
import select
import subprocess
import sys
import tempfile
from argparse import Namespace
from typing import Optional

import yaml
from assistants import version
from assistants.ai.anthropic import Claude
from assistants.ai.constants import REASONING_MODELS
from assistants.ai.dummy_assistant import DummyAssistant
from assistants.ai.openai import Assistant, Completion
from assistants.ai.types import AssistantInterface
from assistants.cli import output
from assistants.config import Config, environment
from assistants.lib.exceptions import ConfigError
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound
from pygments_tsx.tsx import TypeScriptXLexer, patch_pygments

fallback_lexers = {
    "tsx": TypeScriptXLexer,
    "plaintext": TextLexer,
}


def highlight_code_blocks(markdown_text):
    """
    Highlight code blocks in markdown text using Pygments.
    """
    patch_pygments()
    code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

    def replacer(match):
        lang = match.group(1)
        code = match.group(2)
        if lang:
            lexer_class = fallback_lexers.get(lang)
            if not lexer_class:
                try:
                    lexer = get_lexer_by_name(lang, stripall=True)
                except ClassNotFound:
                    lexer = TextLexer()
            else:
                lexer = lexer_class()
        else:
            lexer = get_lexer_by_name("text", stripall=True)
        return f"```{lang if lang else ''}\n{highlight(code, lexer, TerminalFormatter())}```"

    return code_block_pattern.sub(replacer, markdown_text)


def get_text_from_default_editor(initial_text=None):
    """
    Open a text editor to get input from the user.
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
        temp_file_path = temp_file.name

    if initial_text:
        with open(temp_file_path, "w", encoding="utf-8") as text_file:
            text_file.write(initial_text)

    # Open the editor for the user to input text
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, temp_file_path], check=True)

    # Read the contents of the file after the editor is closed
    with open(temp_file_path, "r", encoding="utf-8") as file:
        text = file.read()

    # Remove the temporary file
    os.remove(temp_file_path)

    return text


MODEL_LOOKUP = {
    "code": {
        "o1": Completion,
        "o3": Completion,
        "claude-": Claude,
        "o4-mini": Completion,
    },
    "default": {
        "claude-": Claude,
        "dummy-model": DummyAssistant,
        "gpt-4o": Assistant,
        "o1": Assistant,
        "o3": Assistant,
        "o4": Assistant,
    },
}


async def create_assistant_and_thread(
    args: Namespace, env: Config
) -> tuple[AssistantInterface, Optional[str]]:
    thread_id = None
    instructions = env.ASSISTANT_INSTRUCTIONS

    if args.instructions:
        with open(args.instructions, "r", encoding="utf-8") as file:
            instructions = file.read()

    def get_model_class(model_type: str, model_name: str):
        for key, assistant_type in MODEL_LOOKUP[model_type].items():
            if model_name.startswith(key):
                return assistant_type
        raise ConfigError(f"Invalid {model_type} model: {model_name}")

    if args.code:
        model_class = get_model_class("code", env.CODE_MODEL)
        assistant = model_class(model=env.CODE_MODEL)
        if isinstance(assistant, Claude):
            assistant.thinking = True
    else:
        model_class = get_model_class("default", args.model)

        if model_class == Assistant:
            assistant = model_class(
                name=env.ASSISTANT_NAME,
                model=args.model,
                instructions=instructions,
                tools=[{"type": "code_interpreter"}],
                thinking=args.thinking,
            )
        elif model_class == Claude:
            assistant = model_class(
                model=args.model,
                instructions=(
                    instructions if instructions != env.ASSISTANT_INSTRUCTIONS else None
                ),
                thinking=bool(args.thinking),
            )
        else:
            assistant = model_class(model=args.model)

    await assistant.start()

    if args.continue_thread:
        thread_id = await assistant.async_get_conversation_id()

    return assistant, thread_id


def read_config_file(config_file_path):
    """Read and parse the configuration file."""
    try:
        with open(config_file_path) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        output.fail(f"Error: The file '{config_file_path}' was not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        output.fail(f"Error: {e}")
        sys.exit(1)


def get_initial_input(args):
    """Get initial input from stdin, prompt arguments, editor, or file."""
    # Check for stdin input
    if select.select([sys.stdin], [], [], 0.0)[0]:
        stdin = sys.stdin.read()
        if stdin:
            args.prompt = args.prompt or []
            args.prompt += stdin.split(" ")

    # Join arguments into a single string
    initial_input = " ".join(args.prompt) if args.prompt else None

    # Handle editor mode
    if args.editor:
        return get_text_from_default_editor(initial_input)

    # Handle input file
    if args.input_file:
        try:
            with open(args.input_file, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            output.fail(f"Error: The file '{args.input_file}' was not found.")
            sys.exit(1)

    return initial_input


def validate_args(args):
    """Validate CLI arguments."""
    if args.thinking and (args.thinking > 2 or args.thinking < 0):
        output.fail("Error: The 'thinking' level must be between 0 and 2.")
        sys.exit(1)

    # Set default model if not provided
    if not args.model:
        args.model = environment.DEFAULT_MODEL

    return args


def display_welcome_message(args):
    """Display welcome message with version and model information."""
    model_info = f"'{environment.CODE_MODEL if args.code else args.model}'"
    mode_info = ""
    if args.code:
        mode_info = " (reasoning mode)"
    elif args.thinking and args.model in REASONING_MODELS:
        mode_info = f" (thinking level {args.thinking})"
    elif args.model.startswith("claude") and args.thinking:
        mode_info = " (thinking)"

    output.output(
        f"Assistant CLI v{version.__VERSION__}; using {model_info} model{mode_info}.\n"
        "Type '/help' (or '/h') for a list of commands."
    )
