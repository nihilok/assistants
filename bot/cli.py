import sys

from bot.ai.assistant import Assistant
from bot.config.environment import DEFAULT_MODEL, ASSISTANT_INSTRUCTIONS
from bot.exceptions import NoResponseError


class TerminalColours:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def cli():
    assistant = Assistant(
        "AI Assistant",
        DEFAULT_MODEL,
        ASSISTANT_INSTRUCTIONS,
        tools=[{"type": "code_interpreter"}],
    )
    last_message = None
    try:
        while (user_input := input(TerminalColours.OKGREEN + ">>> ")).lower() not in {
            "q",
            "quit",
        }:
            print(TerminalColours.ENDC, end="")
            message = assistant.converse(
                user_input, last_message.thread_id if last_message else None
            )

            if last_message and message.id == last_message.id:
                raise NoResponseError

            last_message = message
            print(message.content[0].text.value, end="\n\n")

    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
