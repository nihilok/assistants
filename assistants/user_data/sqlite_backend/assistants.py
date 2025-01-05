from typing import NamedTuple, Optional

import aiosqlite

from assistants.config.file_management import DB_PATH

TABLE_NAME = "assistants"


class AssistantData(NamedTuple):
    assistant_id: Optional[str]
    config_hash: Optional[str]


async def get_assistant_data(assistant_name: str, config_hash: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with await db.execute(
            f"SELECT assistant_id, config_hash FROM {TABLE_NAME} WHERE assistant_name = '{assistant_name}';"
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                return AssistantData(*result)

        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES ('{assistant_name}', NULL, '{config_hash}');"
        )
        await db.commit()
        return AssistantData(None, config_hash)


async def save_assistant_id(assistant_name: str, assistant_id: str, config_hash: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES ('{assistant_name}', '{assistant_id}', '{config_hash}');"
        )
        await db.commit()
