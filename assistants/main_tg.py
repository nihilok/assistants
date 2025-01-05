import os
import sys

from assistants.log import logger

try:
    from assistants.telegram_ui import build_bot, run_polling
except ImportError:
    logger.error(
        "Could not import required modules. Install with `pip install assistants[telegram]`"
    )
    sys.exit(1)


BOT_TOKEN = os.getenv("TG_BOT_TOKEN")


def main():
    if BOT_TOKEN is None:
        print("Please set the TG_BOT_TOKEN environment variable.")
        return

    run_polling(build_bot(BOT_TOKEN))


if __name__ == "__main__":
    main()
