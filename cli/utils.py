import os

import pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
import re


PERSISTENT_THREAD_ID_FILE = f"{os.environ.get('HOME', '.')}/.assistant-last-thread-id"


def highlight_code_blocks(markdown_text):
    code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

    def replacer(match):
        lang = match.group(1)
        code = match.group(2)
        if lang:
            lexer = get_lexer_by_name(lang, stripall=True)
        else:
            lexer = get_lexer_by_name("text", stripall=True)
        return highlight(code, lexer, TerminalFormatter())

    return code_block_pattern.sub(replacer, markdown_text)


def get_thread_id():
    try:
        with open(PERSISTENT_THREAD_ID_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None
