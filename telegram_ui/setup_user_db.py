import asyncio

from telegram_ui.sqlite_user_data import SqliteUserData

if __name__ == "__main__":
    user_data = SqliteUserData()
    asyncio.run(user_data.create_db())
