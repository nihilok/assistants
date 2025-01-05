import aiosqlite

from assistants.config.file_management import DB_PATH
from assistants.user_data.sqlite_backend.assistants import TABLE_NAME as ASSISTANTS
from assistants.user_data.sqlite_backend.chat_history import TABLE_NAME as CHAT_HISTORY
from assistants.user_data.sqlite_backend.threads import TABLE_NAME as THREADS


async def init_db():
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {CHAT_HISTORY} (chat_id INTEGER PRIMARY KEY, history TEXT);"
        )
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {ASSISTANTS} (assistant_name TEXT PRIMARY KEY, assistant_id TEXT, config_hash TEXT);"
        )
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {THREADS} (thread_id TEXT PRIMARY KEY, assistant_id TEXT, last_run_dt TEXT);"
        )

        await db.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
