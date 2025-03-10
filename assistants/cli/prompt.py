import sys
from dataclasses import dataclass
from enum import Enum

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from assistants.cli.terminal import clear_screen
from assistants.config.file_management import CONFIG_DIR


class PromptStyle(Enum):
    USER_INPUT = "ansigreen"
    PROMPT_SYMBOL = "ansibrightgreen"


INPUT_CLASSNAME = "input"


@dataclass
class PromptConfig:
    style: Style = Style.from_dict(
        {
            "": PromptStyle.USER_INPUT.value,
            INPUT_CLASSNAME: PromptStyle.PROMPT_SYMBOL.value,
        }
    )
    prompt_symbol: str = ">>>"
    history_file: str = f"{CONFIG_DIR}/history"


bindings = KeyBindings()
config = PromptConfig()
history = FileHistory(config.history_file)
PROMPT = [(f"class:{INPUT_CLASSNAME}", f"{config.prompt_symbol} ")]


@bindings.add("c-l")
def _(_event):
    clear_screen()


def get_user_input() -> str:
    """Get user input from interactive/styled prompt (prompt_toolkit)."""
    if not sys.stdin.isatty():
        sys.stdin = open("/dev/tty")
    return prompt(PROMPT, style=config.style, history=history, in_thread=True)
