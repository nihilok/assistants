import sys


class ANSIEscapeSequence:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"  # (e.g. Orange)
    FAIL = "\033[91m"  # (e.g. Red)
    ENDC = "\033[0m"  # Reset to default
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    # Clear the screen and move the cursor to the top left corner
    CLEAR_SCREEN = "\033[2J\033[H"


def clear_screen():
    """Clear the terminal screen, terminal must be ANSI escape sequence compatible"""
    sys.stdout.write(ANSIEscapeSequence.CLEAR_SCREEN)
    sys.stdout.flush()
