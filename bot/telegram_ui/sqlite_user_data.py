import json

from bot.telegram_ui.user_data import UserData, ChatHistory, NotAuthorized
import urllib.parse

import aiosqlite


class SqliteUserData(UserData):

    async def create_db(self):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS chat_history (chat_id INTEGER PRIMARY KEY, history TEXT);"
            )
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS authorised_users (user_id INTEGER PRIMARY KEY);"
            )
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS authorised_chats (chat_id INTEGER PRIMARY KEY);"
            )
            await db.commit()

    async def get_chat_history(self, chat_id: int) -> ChatHistory:
        async with aiosqlite.connect(self.DB) as db:
            async with await db.execute(
                f"SELECT history FROM chat_history WHERE chat_id = {chat_id};"
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    if history := result[0]:
                        return ChatHistory(
                            **json.loads(urllib.parse.unquote_plus(history))
                        )
            await db.execute(f"REPLACE INTO chat_history VALUES ({chat_id}, NULL);")
            await db.commit()
            return ChatHistory(chat_id=chat_id, history=[])

    async def save_chat_history(self, history: ChatHistory):
        encoded = urllib.parse.quote_plus(json.dumps(history.history))
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(
                f"REPLACE INTO chat_history VALUES ({history.chat_id}, '{encoded}');"
            )
            await db.commit()

    async def check_user_authorised(self, user_id: int):
        async with aiosqlite.connect(self.DB) as db:
            async with await db.execute(
                f"SELECT user_id FROM authorised_users WHERE user_id = {user_id};"
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return True
        raise NotAuthorized(str(user_id))

    async def check_chat_authorised(self, chat_id: int):
        async with aiosqlite.connect(self.DB) as db:
            async with await db.execute(
                f"SELECT user_id FROM authorised_users WHERE chat_id = {chat_id};"
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return True
        raise NotAuthorized(str(chat_id))
