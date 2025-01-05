import asyncio

from assistants.telegram_ui.sqlite_user_data import SqliteUserData
from assistants.user_data.sqlite_backend import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
    user_data = SqliteUserData()
    asyncio.run(user_data.create_db())
