import os

from telegram_ui.tg_bot import build_bot, run_polling

if __name__ == "__main__":
    BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
    run_polling(build_bot(BOT_TOKEN))
