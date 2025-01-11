import os

import aiosqlite

from assistants.config.file_management import DB_PATH
from assistants.log import logger
from assistants.user_data.sqlite_backend.assistants import TABLE_NAME as ASSISTANTS
from assistants.user_data.sqlite_backend.chat_history import TABLE_NAME as CHAT_HISTORY
from assistants.user_data.sqlite_backend.conversations import conversations_table
from assistants.user_data.sqlite_backend.telegram_chat_data import telegram_data
from assistants.user_data.sqlite_backend.threads import TABLE_NAME as THREADS


async def table_exists(db_path, table_name):
    async with aiosqlite.connect(db_path) as db:
        try:
            # Query to check for the table in sqlite_master
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,),
            ) as cursor:
                result = await cursor.fetchone()
                return result is not None  # If result is not None, the table exists
        except aiosqlite.Error as e:
            print(f"An error occurred while checking for the table: {e}")
            return False


async def column_exists(db_path, table_name, column_name):
    async with aiosqlite.connect(db_path) as db:
        try:
            # Execute the PRAGMA statement to get column info
            async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
                columns = await cursor.fetchall()
                # Check if the column exists in the returned columns
                for column in columns:
                    if column[1] == column_name:  # column[1] is the column name
                        return True
        except aiosqlite.Error as e:
            print(f"An error occurred: {e}")
            # Return False or handle the error as needed, e.g., table doesn't exist.
            return False
    return False


async def drop_table(db_path, table_name):
    async with aiosqlite.connect(db_path) as db:
        try:
            # Execute the DROP TABLE statement
            await db.execute(f"DROP TABLE IF EXISTS {table_name};")
            await db.commit()  # Commit the changes
            print(f"Table '{table_name}' has been dropped successfully.")
        except aiosqlite.Error as e:
            print(f"An error occurred while dropping the table: {e}")


async def init_db():
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {ASSISTANTS} (assistant_name TEXT PRIMARY KEY, assistant_id TEXT, config_hash TEXT);"
        )
        await db.execute(
            f"CREATE TABLE IF NOT EXISTS {THREADS} (thread_id TEXT PRIMARY KEY, assistant_id TEXT, last_run_dt TEXT, initial_prompt TEXT);"
        )

        await db.commit()

        await conversations_table.create_table()

        if os.getenv("TELEGRAM_DATA"):
            # Handle an old version of DB where this table was created in error
            if await table_exists(DB_PATH, CHAT_HISTORY):
                if not await column_exists(DB_PATH, CHAT_HISTORY, "thread_id"):
                    await drop_table(DB_PATH, CHAT_HISTORY)

            await telegram_data.create_db()


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
