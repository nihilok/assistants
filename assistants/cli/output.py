import sys
from assistants.cli.terminal import ANSIEscapeSequence


def reset():
    print(ANSIEscapeSequence.ENDC, end="")


def new_line(n=1):
    print("\n" * n, end="")


def green(text: str):
    print(f"{ANSIEscapeSequence.OKGREEN}{text if text else ''}", end="")


def warning(text: str):
    print(f"{ANSIEscapeSequence.WARNING}{text if text else ''}", end="")


def info(text: str):
    print(f"{ANSIEscapeSequence.OKBLUE}{text if text else ''}", end="")


def error(text: str):
    print(f"{ANSIEscapeSequence.FAIL}{text if text else ''}", end="")


def default(text: str):
    print(f"{ANSIEscapeSequence.ENDC}{text if text else ''}", end="")


def output(text: str):
    default(text)
    new_line(2)
    reset()


def warn(text: str):
    warning(text)
    new_line(2)
    reset()


def fail(text: str):
    error(text)
    new_line(2)
    reset()


def inform(text: str):
    info(text)
    new_line(2)
    reset()


def user_input(text: str, prompt: str = ">>>"):
    green(f"{prompt} {text}")
    new_line()
    reset()


def update_line(text: str):
    """Updates the current line in the console."""
    sys.stdout.write(f"\r{text}")
    sys.stdout.flush()
