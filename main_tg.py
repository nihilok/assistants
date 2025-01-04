import os

from telegram_ui.tg_bot import build_bot, run_polling

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")


def main():
    if BOT_TOKEN is None:
        print("Please set the TG_BOT_TOKEN environment variable.")
        return

    run_polling(build_bot(BOT_TOKEN))


if __name__ == "__main__":
    main()
