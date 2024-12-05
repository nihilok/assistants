import os

PERSISTENT_THREAD_ID_FILE = f"{os.environ.get('HOME', '.')}/.assistant-last-thread-id"


def get_thread_id():
    try:
        with open(PERSISTENT_THREAD_ID_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None
