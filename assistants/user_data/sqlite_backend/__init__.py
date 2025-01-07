import os

import aiosqlite

from assistants.config.file_management import DB_PATH
from assistants.log import logger
from assistants.user_data.sqlite_backend.assistants import TABLE_NAME as ASSISTANTS
from assistants.user_data.sqlite_backend.chat_history import TABLE_NAME as CHAT_HISTORY
from assistants.user_data.sqlite_backend.conversations import conversations_table
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
            f"CREATE TABLE IF NOT EXISTS {THREADS} (thread_id TEXT PRIMARY KEY, assistant_id TEXT, last_run_dt TEXT, initial_prompt TEXT);"
        )

        await db.commit()

        await conversations_table.create_table()


async def rebuild_db():
    if DB_PATH.exists():
        # Create backup of existing database in /tmp
        backup_file = DB_PATH.with_suffix(".bak")
        backup_file.write_bytes(DB_PATH.read_bytes())
        os.rename(backup_file, f"/tmp/{backup_file.name}")
        logger.info(f"Existing database backed up to /tmp/{backup_file.name}")
        DB_PATH.unlink()

    if DB_PATH.exists():
        raise RuntimeError("Failed to delete existing database")

    await init_db()
