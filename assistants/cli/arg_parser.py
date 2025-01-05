import argparse

from assistants import version


def get_args():
    parser = argparse.ArgumentParser(
        description=f"CLI for AI Assistant v{version.__VERSION__}"
    )
    parser.add_argument(
        "-e",
        "--editor",
        action="store_true",
        help="Open the default editor to compose a prompt.",
    )
    parser.add_argument(
        "-f",
        "--input-file",
        metavar="INPUT_FILE",
        type=str,
        help="Read the initial prompt from a file (e.g., 'input.txt').",
    )
    parser.add_argument(
        "-i",
        "--instructions",
        metavar="INSTRUCTIONS_FILE",
        type=str,
        help="Read the initial instructions (system message) from a specified file; "
        "if not provided, environment variable `ASSISTANT_INSTRUCTIONS` or defaults "
        "will be used.",
    )
    parser.add_argument(
        "-t",
        "--continue-thread",
        action="store_true",
        help="Continue previous thread. (not currently possible with `-C` option)",
    )
    parser.add_argument(
        "-C",
        "--code",
        action="store_true",
        help="Use specialised reasoning/code model. WARNING: This model will be slower "
        "and more expensive to use.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Positional arguments concatenate into a single prompt. E.g. `ai-cli "
        "Is this a single prompt\\?` (question mark escaped)\n"
        "...will be passed to the program as a single string (without the backslash). You "
        "can also use quotes to pass a single argument with spaces and special characters. "
        "See the -e and -f options for more advanced prompt options.",
    )
    args = parser.parse_args()
    return args
