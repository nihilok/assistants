import json

import aiosqlite

from assistants.user_data.interfaces.telegram_chat_data import (
    ChatHistory,
    NotAuthorized,
    UserData,
)


class TelegramSqliteUserData(UserData):
    async def create_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """\
                CREATE TABLE IF NOT EXISTS authorised_chats (
                    chat_id INTEGER PRIMARY KEY
                );
                """
            )
            await db.execute(
                """\
                CREATE TABLE IF NOT EXISTS chat_history (
                    chat_id INTEGER,
                    thread_id TEXT,
                    auto_reply BOOLEAN DEFAULT TRUE,
                    PRIMARY KEY (chat_id),
                    FOREIGN KEY (chat_id) REFERENCES authorised_chats(chat_id)
                );
                """
            )
            await db.execute(
                """\
                CREATE TABLE IF NOT EXISTS authorised_users (
                    user_id INTEGER PRIMARY KEY
                );
                """
            )
            await db.execute(
                """\
                CREATE TABLE IF NOT EXISTS superusers (
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES authorised_users(user_id),
                    PRIMARY KEY (user_id)
                );
                """
            )

            await db.commit()

    async def get_chat_history(self, chat_id: int) -> ChatHistory:
        async with aiosqlite.connect(self.DB) as db:
            async with await db.execute(
                f"""\
                SELECT thread_id, auto_reply
                FROM chat_history
                WHERE chat_id = {chat_id};
                """
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    thread_id, auto_reply = result
                    return ChatHistory(
                        chat_id=chat_id, thread_id=thread_id, auto_reply=auto_reply
                    )
            await db.execute(
                f"REPLACE INTO chat_history VALUES ({chat_id}, NULL, true);"
            )
            await db.commit()
            return ChatHistory(chat_id=chat_id, thread_id=None, auto_reply=True)

    async def save_chat_history(self, history: ChatHistory):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(
                f"""\
                REPLACE INTO chat_history VALUES (
                    {history.chat_id},
                    '{history.thread_id}',
                    {json.dumps(history.auto_reply)}
                );
                """
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

    async def check_superuser(self, user_id: int):
        async with aiosqlite.connect(self.DB) as db:
            async with await db.execute(
                f"SELECT user_id FROM superusers WHERE user_id = {user_id};"
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return True
        raise NotAuthorized(str(user_id))

    async def check_chat_authorised(self, chat_id: int):
        async with aiosqlite.connect(self.DB) as db:
            async with await db.execute(
                f"SELECT chat_id FROM authorised_chats WHERE chat_id = {chat_id};"
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return True
        raise NotAuthorized(str(chat_id))

    async def authorise_user(self, user_id: int):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(f"REPLACE INTO authorised_users VALUES ({user_id});")
            await db.commit()

    async def promote_superuser(self, user_id: int):
        await self.authorise_user(user_id)
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(f"REPLACE INTO superusers VALUES ({user_id});")
            await db.commit()

    async def demote_superuser(self, user_id: int):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(f"DELETE FROM superusers WHERE user_id = {user_id};")
            await db.commit()

    async def authorise_chat(self, chat_id: int):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(f"REPLACE INTO authorised_chats VALUES ({chat_id});")
            await db.commit()

    async def deauthorise_user(self, user_id: int):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(f"DELETE FROM authorised_users WHERE user_id = {user_id};")
            await db.commit()

    async def deauthorise_chat(self, chat_id: int):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(f"DELETE FROM authorised_chats WHERE chat_id = {chat_id};")
            await db.commit()

    async def clear_last_thread_id(self, chat_id: int):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(
                f"UPDATE chat_history SET thread_id = NULL WHERE chat_id = {chat_id};"
            )
            await db.commit()

    async def set_auto_reply(self, chat_id: int, auto_reply: bool):
        async with aiosqlite.connect(self.DB) as db:
            await db.execute(
                f"""\
                UPDATE chat_history
                SET auto_reply = {json.dumps(auto_reply)}
                WHERE chat_id = {chat_id};
                """
            )
            await db.commit()


telegram_data = TelegramSqliteUserData()
