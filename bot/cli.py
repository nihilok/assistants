import sys

from bot.ai.assistant import Assistant
from bot.config.environment import DEFAULT_MODEL, ASSISTANT_INSTRUCTIONS
from bot.exceptions import NoResponseError
from bot.helpers import get_text_from_default_editor


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
    user_input = ""

    opts = sys.argv[1:]

    if "-e" in opts:
        initial_input = get_text_from_default_editor()
    elif opts:
        initial_input = " ".join(opts)
    else:
        initial_input = ""

    assistant = Assistant(
        "AI Assistant",
        DEFAULT_MODEL,
        ASSISTANT_INSTRUCTIONS,
        tools=[{"type": "code_interpreter"}],
    )
    last_message = None
    try:
        while initial_input or (
            user_input := input(TerminalColours.OKGREEN + ">>> ")
        ).lower() not in {
            "q",
            "quit",
        }:
            if initial_input:
                print(initial_input)

            elif not user_input:
                continue

            elif user_input.strip() == "-e":
                user_input = get_text_from_default_editor()

                if not user_input:
                    continue

                print(user_input)

            print(TerminalColours.ENDC, end="")

            message = assistant.converse(
                initial_input or user_input,
                last_message.thread_id if last_message else None,
            )

            initial_input = ""  # Only relevant for first iteration (comes from initial command line)

            if last_message and message.id == last_message.id:
                raise NoResponseError

            last_message = message
            print(message.content[0].text.value, end="\n\n")

    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
