import asyncio

from bot.telegram_ui.sqlite_user_data import SqliteUserData
from bot.user_data.sqlite_backend import init_db

asyncio.run(init_db())
user_data = SqliteUserData()
asyncio.run(user_data.create_db())
