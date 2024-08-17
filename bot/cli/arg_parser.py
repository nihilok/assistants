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
        help="Read the initial instructions (system message) from a specified file "
        "(if not provided, environment variables or defaults will be used).",
    )
    parser.add_argument(
        "-t",
        action="store_true",
        help="Continue previous thread.",
    )
    parser.add_argument(
        "positional_args",
        nargs="*",
        help="Positional arguments to concatenate into a single prompt. E.g. ./cli.py This is a single prompt.",
    )
    args = parser.parse_args()
    return args
