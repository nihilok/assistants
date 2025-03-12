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
            cur = await conn.cursor()
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
            return results

    async def save_thread(
        self, thread_id: str, assistant_id: str, initial_prompt: Optional[str] = None
    ) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            # Select the initial prompt for the thread_id if it exists
            async with await conn.execute(
                "SELECT initial_prompt FROM {TABLE_NAME} WHERE thread_id = ?;",
                (thread_id,),
            ) as cursor:
                result = await cursor.fetchone()
                initial_prompt = result[0] if result else initial_prompt
            await conn.execute(
                f"REPLACE INTO {TABLE_NAME} VALUES (?, ?, ?, ?);",
                (thread_id, assistant_id, datetime.now().isoformat(), initial_prompt),
            )
            await conn.commit()


threads_table = ThreadsTable()


async def get_last_thread_for_assistant(assistant_id: str) -> Optional[ThreadData]:
    result = await threads_table.get_by_assistant_id(assistant_id, limit=1)
    if result:
        return result[0]
    return None
