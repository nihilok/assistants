import json
import urllib.parse

import aiosqlite

from assistants.config.file_management import DB_PATH

TABLE_NAME = "chat_history"


async def get_user_data(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with await db.execute(
            f"SELECT history FROM {TABLE_NAME} WHERE chat_id = {chat_id};"
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                if result[0]:
                    return json.loads(urllib.parse.unquote_plus(result[0]))
        await db.execute(f"REPLACE INTO {TABLE_NAME} VALUES ({chat_id}, NULL);")
        await db.commit()
        return []


async def store_user_data(chat_id: int, history: list[dict[str, str]]):
    encoded = urllib.parse.quote_plus(json.dumps(history))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"REPLACE INTO {TABLE_NAME} VALUES ({chat_id}, '{encoded}');")
        await db.commit()
