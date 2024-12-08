import argparse


def get_args():
    parser = argparse.ArgumentParser(description="CLI for AI Assistant")
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
        "positional_args",
        nargs="*",
        help="Positional arguments to concatenate into a single prompt. E.g. ./cli.py "
        "This is a single prompt.",
    )
    args = parser.parse_args()
    return args
