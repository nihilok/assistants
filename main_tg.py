import os

from bot.telegram_ui.tg_bot import run_polling, build_bot


if __name__ == "__main__":
    BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    run_polling(build_bot(BOT_TOKEN))
