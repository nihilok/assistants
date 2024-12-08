import aiosqlite

from user_data.sqlite_backend.constants import DB_TABLE

TABLE_NAME = "assistants"


async def get_assistant_id(assistant_name: str, config_hash: str):
    async with aiosqlite.connect(DB_TABLE) as db:
        async with await db.execute(
            f"SELECT assistant_id, config_hash FROM {TABLE_NAME} WHERE assistant_name = '{assistant_name}';"
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                if result:
                    return result[0], result[1]

        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES ('{assistant_name}', NULL, '{config_hash}');"
        )
        await db.commit()
        return []


async def save_assistant_id(assistant_name: str, assistant_id: str, config_hash: str):
    async with aiosqlite.connect(DB_TABLE) as db:
        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES ('{assistant_name}', '{assistant_id}', '{config_hash}');"
        )
        await db.commit()
