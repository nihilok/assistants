import os

import aiosqlite

from assistants.config.file_management import DB_PATH
from assistants.log import logger
from assistants.user_data.sqlite_backend.conversations import (
    get_conversations_table,
)
from assistants.user_data.sqlite_backend.message import (
    get_messages_table,
)
from assistants.user_data.sqlite_backend.telegram_chat_data import (
    get_telegram_data,
)


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

    await get_conversations_table().create_table()
    await get_messages_table().create_table()

    if os.getenv("TELEGRAM_DATA"):
        await get_telegram_data().create_db()


async def rebuild_db():
    if DB_PATH.exists():
        # Create backup of existing database in /tmp
        backup_file = DB_PATH.with_suffix(".bak")
        backup_file.write_bytes(DB_PATH.read_bytes())
        logger.info(f"Existing database backed up to {backup_file}")
        DB_PATH.unlink()

    if DB_PATH.exists():
        raise RuntimeError("Failed to delete existing database")

    # Drop tables using the new table classes
    if os.getenv("TELEGRAM_DATA"):
        await get_telegram_data().authorised_chats_table.drop_table()
        await get_telegram_data().authorised_users_table.drop_table()
        await get_telegram_data().superusers_table.drop_table()
        await get_telegram_data().chat_history_table.drop_table()

    await get_conversations_table().drop_table()

    # Drop legacy tables that might still exist
    await drop_table(DB_PATH, "responses")
    await drop_table(DB_PATH, "threads")
    await drop_table(DB_PATH, "assistants")
    await drop_table(DB_PATH, "chat_history")  # From the old chat_history.py module

    await init_db()


async def migrate():
    """
    Run the migration script to ensure the database is up-to-date.
    """
    if not DB_PATH.exists():
        raise RuntimeError("Database does not exist. Please run init_db() first.")

    # Create tables if they do not exist
    if not await table_exists(DB_PATH, "conversations"):
        logger.info("Conversations table does not exist. Creating it.")
        await get_conversations_table().create_table()

    if os.getenv("TELEGRAM_DATA"):
        if not await table_exists(DB_PATH, "authorised_chats"):
            logger.info("Authorised chats table does not exist. Creating it.")
            await get_telegram_data().authorised_chats_table.create_table()

        if not await table_exists(DB_PATH, "authorised_users"):
            logger.info("Authorised users table does not exist. Creating it.")
            await get_telegram_data().authorised_users_table.create_table()

        if not await table_exists(DB_PATH, "superusers"):
            logger.info("Superusers table does not exist. Creating it.")
            await get_telegram_data().superusers_table.create_table()

        if not await table_exists(DB_PATH, "chat_history"):
            logger.info("Chat history table does not exist. Creating it.")
            await get_telegram_data().chat_history_table.create_table()

    # Run migrations for all tables
    for table in [
        get_telegram_data().authorised_chats_table,
        get_telegram_data().authorised_users_table,
        get_telegram_data().superusers_table,
        get_telegram_data().chat_history_table,
        get_conversations_table(),
        get_messages_table(),
    ]:
        await table.migrate_if_needed()

    logger.info("Database migration completed successfully.")
