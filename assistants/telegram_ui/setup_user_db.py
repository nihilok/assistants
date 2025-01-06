import asyncio

from assistants.telegram_ui.sqlite_user_data import TelegramSqliteUserData

if __name__ == "__main__":
    user_data = TelegramSqliteUserData()
    asyncio.run(user_data.create_db())
