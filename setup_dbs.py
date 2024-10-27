import asyncio
import os

from bot.telegram_ui.sqlite_user_data import SqliteUserData
from bot.user_data.sqlite_backend import init_db

os.environ.setdefault("TG_USER_DATA", "tg_user_data.db")
os.environ.setdefault("USER_DATA_DB", "assistant_data.db")

asyncio.run(init_db())
user_data = SqliteUserData()
asyncio.run(user_data.create_db())
