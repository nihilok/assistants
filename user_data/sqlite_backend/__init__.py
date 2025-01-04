import aiosqlite

from user_data.sqlite_backend.assistants import TABLE_NAME as ASSISTANTS
from user_data.sqlite_backend.chat_history import TABLE_NAME as CHAT_HISTORY
from config import DB_TABLE


async def init_db():
    async with aiosqlite.connect(DB_TABLE) as db:
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {CHAT_HISTORY} (chat_id INTEGER PRIMARY KEY, history TEXT);"
        )
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {ASSISTANTS} (assistant_name TEXT PRIMARY KEY, assistant_id TEXT, config_hash TEXT);"
        )
        await db.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
