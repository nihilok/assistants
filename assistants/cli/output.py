import sys
from assistants.cli.terminal import ANSIEscapeSequence


def reset():
    print(f"{ANSIEscapeSequence.ENDC}", end="")


def new_line(n=1):
    print("\n" * n, end="")


def green(text: str):
    print(f"{ANSIEscapeSequence.OKGREEN}{text if text else ''}", end="")
    reset()


def warning(text: str):
    print(f"{ANSIEscapeSequence.WARNING}{text if text else ''}", end="")
    reset()


def info(text: str):
    print(f"{ANSIEscapeSequence.OKBLUE}{text if text else ''}", end="")
    reset()


def error(text: str):
    print(f"{ANSIEscapeSequence.FAIL}{text if text else ''}", end="")
    reset()


def default(text: str):
    print(f"{ANSIEscapeSequence.ENDC}{text if text else ''}", end="")
    reset()


def output(text: str):
    default(text)
    new_line(2)


def warn(text: str):
    warning(text)
    new_line(2)


def fail(text: str):
    error(text)
    new_line(2)


def inform(text: str):
    info(text)
    new_line(2)


def user_input(text: str, prompt: str = ">>>"):
    green(f"{prompt} {text}")
    new_line()


def update_line(text: str):
    """Updates the current line in the console."""
    sys.stdout.write(f"\r{text}")
    sys.stdout.flush()
