import json
import os
import urllib.parse
import aiosqlite

DB_TABLE = os.environ.get("ACCOUNTABILIBOT_USER_DATA_DB", "user_data.sqlite")


async def init_db():
    async with aiosqlite.connect(DB_TABLE) as db:
        await db.execute(f"CREATE TABLE IF NOT EXISTS chat_history (chat_id INTEGER PRIMARY KEY, history TEXT);")
        await db.commit()


async def get_user_data(chat_id: int):
    async with aiosqlite.connect(DB_TABLE) as db:
        async with await db.execute(f"SELECT history FROM chat_history WHERE chat_id = {chat_id};") as cursor:
            result = await cursor.fetchone()
            if result:
                if result[0]:
                    return json.loads(urllib.parse.unquote_plus(result[0]))
        await db.execute(f"REPLACE INTO chat_history VALUES ({chat_id}, NULL);")
        await db.commit()
        return []


async def store_user_data(chat_id: int, history: list[dict[str, str]]):
    encoded = urllib.parse.quote_plus(json.dumps(history))
    async with aiosqlite.connect(DB_TABLE) as db:
        await db.execute(f"REPLACE INTO chat_history VALUES ({chat_id}, '{encoded}');")
        await db.commit()


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
