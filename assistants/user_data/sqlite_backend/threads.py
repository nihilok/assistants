from datetime import datetime
from typing import NamedTuple, Optional

import aiosqlite

from assistants.config.file_management import DB_PATH

TABLE_NAME = "threads"


class ThreadData(NamedTuple):
    thread_id: str
    last_run_dt: Optional[datetime]
    assistant_id: Optional[str]


class NewThreadData(NamedTuple):
    thread_id: str
    assistant_id: Optional[str]


async def get_last_thread_for_assistant(assistant_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with await db.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE assistant_id = '{assistant_id}'\
            ORDER BY last_run_dt DESC LIMIT 1;"
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                return ThreadData(*result)
        return None


async def save_thread_data(thread_id: str, assistant_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES ('{thread_id}', '{assistant_id}', '{datetime.now()}');"
        )
        await db.commit()
