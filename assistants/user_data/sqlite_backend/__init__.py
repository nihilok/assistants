import os

import aiosqlite

from assistants.config.file_management import DB_PATH
from assistants.log import logger
from assistants.user_data.sqlite_backend.assistants import TABLE_NAME as ASSISTANTS
from assistants.user_data.sqlite_backend.chat_history import TABLE_NAME as CHAT_HISTORY
from assistants.user_data.sqlite_backend.conversations import conversations_table
from assistants.user_data.sqlite_backend.telegram_chat_data import telegram_data


async def table_exists(db_path, table_name):
    async with aiosqlite.connect(db_path) as db:
        try:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,),
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None  # If result is not None, the table exists
        except aiosqlite.Error as e:
            print(f"An error occurred while checking for the table: {e}")
            return False


async def drop_table(db_path, table_name):
    async with aiosqlite.connect(db_path) as db:
        try:
            await db.execute(f"DROP TABLE IF EXISTS {table_name};")
            await db.commit()
            print(f"Table '{table_name}' has been dropped successfully.")
        except aiosqlite.Error as e:
            print(f"An error occurred while dropping the table: {e}")


async def init_db():
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True)

    await conversations_table.create_table()

    if os.getenv("TELEGRAM_DATA"):
        await telegram_data.create_db()


async def rebuild_db():
    if DB_PATH.exists():
        # Create backup of existing database in /tmp
        backup_file = DB_PATH.with_suffix(".bak")
        backup_file.write_bytes(DB_PATH.read_bytes())
        logger.info(f"Existing database backed up to {backup_file}")
        DB_PATH.unlink()

    if DB_PATH.exists():
        raise RuntimeError("Failed to delete existing database")

    await drop_table(DB_PATH, ASSISTANTS)
    await drop_table(DB_PATH, CHAT_HISTORY)
    await drop_table(DB_PATH, "responses")
    await drop_table(DB_PATH, "threads")

    await init_db()
