from datetime import datetime
from pathlib import Path
from typing import NamedTuple, Optional

import aiosqlite

from assistants.config.file_management import DB_PATH

TABLE_NAME = "threads"


class ThreadData(NamedTuple):
    thread_id: str
    last_run_dt: Optional[str]
    assistant_id: Optional[str]
    initial_prompt: Optional[str]


class NewThreadData(NamedTuple):
    thread_id: str
    assistant_id: Optional[str]


class ThreadsTable:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    async def get_by_thread_id(self, thread_id: str) -> Optional[ThreadData]:
        async with aiosqlite.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT thread_id, last_run_dt, assistant_id, initial_prompt FROM threads WHERE thread_id = ?",
                (thread_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return ThreadData(*row)

    async def get_by_assistant_id(
        self, assistant_id: str, limit: int = 0
    ) -> list[ThreadData]:
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.cursor()
            statement = (
                "SELECT thread_id, last_run_dt, assistant_id, initial_prompt FROM threads WHERE assistant_id = ?"
                "ORDER BY last_run_dt DESC"
            )
            if limit > 0:
                statement = statement + " LIMIT ?"
                binding = (assistant_id, limit)
            else:
                binding = (assistant_id,)
            await cur.execute(
                statement,
                binding,
            )
            rows = await cur.fetchall()
            results = []
            for row in rows:
                results.append(ThreadData(*row))
            return results

    async def get_all_threads(self) -> list[ThreadData]:
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.cursor()
            await cur.execute(
                "SELECT thread_id, last_run_dt, assistant_id, initial_prompt FROM threads WHERE TRUE "
                "ORDER BY last_run_dt DESC;"
            )
            rows = await cur.fetchall()
            results = []
            for row in rows:
                results.append(ThreadData(*row))


threads_table = ThreadsTable()


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


async def save_thread_data(thread_id: str, assistant_id: str, user_input: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # select the initial prompt for the thread_id if it exists
        async with await db.execute(
            f"SELECT initial_prompt FROM {TABLE_NAME} WHERE thread_id = '{thread_id}';"
        ) as cursor:
            result = await cursor.fetchone()
            initial_prompt = result[0] if result else user_input
        await db.execute(
            f"REPLACE INTO {TABLE_NAME} VALUES (?, ?, ?, ?);",
            (thread_id, assistant_id, datetime.now().isoformat(), initial_prompt),
        )
        await db.commit()
