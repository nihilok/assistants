import aiosqlite

from bot.user_data.sqlite_backend.constants import DB_TABLE

TABLE_NAME = "assistants"


async def get_assistant_id(assistant_name: str):
    async with aiosqlite.connect(DB_TABLE) as db:
        async with await db.execute(
            f"SELECT assistant_id FROM {TABLE_NAME} WHERE assistant_name = '{assistant_name}';"
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                if result[0]:
                    return result[0]

        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES ('{assistant_name}', NULL);"
        )
        await db.commit()
        return []


async def save_assistant_id(assistant_name: str, assistant_id: str):
    async with aiosqlite.connect(DB_TABLE) as db:
        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES ('{assistant_name}', '{assistant_id}');"
        )
        await db.commit()
