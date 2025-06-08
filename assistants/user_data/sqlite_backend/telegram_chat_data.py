"""
This module defines the data models and table classes for Telegram chat data in an SQLite database.

Classes:
    - AuthorisedChat: Pydantic model representing an authorised chat.
    - AuthorisedUser: Pydantic model representing an authorised user.
    - Superuser: Pydantic model representing a superuser.
    - ChatHistory: Pydantic model representing chat history.
    - AuthorisedChatsTable: Table for authorised chats.
    - AuthorisedUsersTable: Table for authorised users.
    - SuperusersTable: Table for superusers.
    - ChatHistoryTable: Table for chat history.
    - TelegramSqliteUserData: Class implementing the UserData interface using the table classes.
"""

import json
from typing import List, Optional

import aiosqlite
from pydantic import BaseModel

from assistants.user_data.interfaces.telegram_chat_data import (
    ChatHistory as ChatHistoryInterface,
    NotAuthorised,
    UserData,
)
from assistants.user_data.sqlite_backend.table import Table


class AuthorisedChat(BaseModel):
    """
    Pydantic model representing an authorised chat.

    Attributes:
        chat_id (int): The unique identifier of the chat.
    """

    chat_id: int


class AuthorisedUser(BaseModel):
    """
    Pydantic model representing an authorised user.

    Attributes:
        user_id (int): The unique identifier of the user.
    """

    user_id: int


class Superuser(BaseModel):
    """
    Pydantic model representing a superuser.

    Attributes:
        user_id (int): The unique identifier of the superuser.
    """

    user_id: int


class ChatHistory(BaseModel):
    """
    Pydantic model representing chat history.

    Attributes:
        chat_id (int): The unique identifier of the chat.
        thread_id (Optional[str]): The thread ID, if any.
        auto_reply (bool): Whether auto-reply is enabled.
    """

    chat_id: int
    thread_id: Optional[str] = None
    auto_reply: bool = True
    history: Optional[str] = None  # JSON string of chat history


class AuthorisedChatsTable(Table[AuthorisedChat]):
    """
    Table for authorised chats.
    """

    def get_table_name(self) -> str:
        return "authorised_chats"

    def get_model_class(self):
        return AuthorisedChat

    def get_create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS authorised_chats (
                chat_id INTEGER PRIMARY KEY
            )
        """

    async def migrate_if_needed(self) -> None:
        # Currently no migrations needed for this table
        pass

    async def insert(self, record: AuthorisedChat) -> None:
        await self.update(record)

    async def update(self, record: AuthorisedChat) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                REPLACE INTO authorised_chats VALUES (?)
                """,
                (record.chat_id,),
            )
            await db.commit()

    async def delete(self, **kwargs) -> None:
        if "chat_id" not in kwargs:
            raise ValueError("Chat ID is required for deletion")

        chat_id = kwargs["chat_id"]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM authorised_chats WHERE chat_id = ?
                """,
                (chat_id,),
            )
            await db.commit()

    async def get(self, **kwargs) -> Optional[AuthorisedChat]:
        if "chat_id" not in kwargs:
            raise ValueError("Chat ID is required")

        chat_id = kwargs["chat_id"]
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT chat_id FROM authorised_chats WHERE chat_id = ?
                """,
                (chat_id,),
            )
            row = await cursor.fetchone()
            if row:
                return AuthorisedChat(chat_id=row[0])
        return None

    async def get_all(self) -> List[AuthorisedChat]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT chat_id FROM authorised_chats
                """
            )
            rows = await cursor.fetchall()
            return [AuthorisedChat(chat_id=row[0]) for row in rows]


class AuthorisedUsersTable(Table[AuthorisedUser]):
    """
    Table for authorised users.
    """

    def get_table_name(self) -> str:
        return "authorised_users"

    def get_model_class(self):
        return AuthorisedUser

    def get_create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS authorised_users (
                user_id INTEGER PRIMARY KEY
            )
        """

    async def migrate_if_needed(self) -> None:
        # Currently no migrations needed for this table
        pass

    async def insert(self, record: AuthorisedUser) -> None:
        await self.update(record)

    async def update(self, record: AuthorisedUser) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                REPLACE INTO authorised_users VALUES (?)
                """,
                (record.user_id,),
            )
            await db.commit()

    async def delete(self, **kwargs) -> None:
        if "user_id" not in kwargs:
            raise ValueError("User ID is required for deletion")

        user_id = kwargs["user_id"]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM authorised_users WHERE user_id = ?
                """,
                (user_id,),
            )
            await db.commit()

    async def get(self, **kwargs) -> Optional[AuthorisedUser]:
        if "user_id" not in kwargs:
            raise ValueError("User ID is required")

        user_id = kwargs["user_id"]
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT user_id FROM authorised_users WHERE user_id = ?
                """,
                (user_id,),
            )
            row = await cursor.fetchone()
            if row:
                return AuthorisedUser(user_id=row[0])
        return None

    async def get_all(self) -> List[AuthorisedUser]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT user_id FROM authorised_users
                """
            )
            rows = await cursor.fetchall()
            return [AuthorisedUser(user_id=row[0]) for row in rows]


class SuperusersTable(Table[Superuser]):
    """
    Table for superusers.
    """

    def get_table_name(self) -> str:
        return "superusers"

    def get_model_class(self):
        return Superuser

    def get_create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS superusers (
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES authorised_users(user_id),
                PRIMARY KEY (user_id)
            )
        """

    async def migrate_if_needed(self) -> None:
        # Currently no migrations needed for this table
        pass

    async def insert(self, record: Superuser) -> None:
        await self.update(record)

    async def update(self, record: Superuser) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                REPLACE INTO superusers VALUES (?)
                """,
                (record.user_id,),
            )
            await db.commit()

    async def delete(self, **kwargs) -> None:
        if "user_id" not in kwargs:
            raise ValueError("User ID is required for deletion")

        user_id = kwargs["user_id"]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM superusers WHERE user_id = ?
                """,
                (user_id,),
            )
            await db.commit()

    async def get(self, **kwargs) -> Optional[Superuser]:
        if "user_id" not in kwargs:
            raise ValueError("User ID is required")

        user_id = kwargs["user_id"]
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT user_id FROM superusers WHERE user_id = ?
                """,
                (user_id,),
            )
            row = await cursor.fetchone()
            if row:
                return Superuser(user_id=row[0])
        return None

    async def get_all(self) -> List[Superuser]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT user_id FROM superusers
                """
            )
            rows = await cursor.fetchall()
            return [Superuser(user_id=row[0]) for row in rows]


class ChatHistoryTable(Table[ChatHistory]):
    """
    Table for chat history.
    """

    def get_table_name(self) -> str:
        return "chat_history"

    def get_model_class(self):
        return ChatHistory

    def get_create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS chat_history (
                chat_id INTEGER,
                thread_id TEXT,
                auto_reply BOOLEAN DEFAULT TRUE,
                chat_history TEXT DEFAULT NULL,
                PRIMARY KEY (chat_id),
                FOREIGN KEY (chat_id) REFERENCES authorised_chats(chat_id)
            )
        """

    async def migrate_if_needed(self) -> None:
        # Add the chat_history column if it doesn't exist
        alter_sql = """
            ALTER TABLE chat_history ADD COLUMN chat_history TEXT DEFAULT NULL
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(alter_sql)
            except aiosqlite.OperationalError as e:
                # If the column already exists, ignore the error
                if "duplicate column name: chat_history" not in str(e):
                    raise

    async def insert(self, record: ChatHistory) -> None:
        await self.update(record)

    async def update(self, record: ChatHistory) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                REPLACE INTO chat_history VALUES (?, ?, ?)
                """,
                (
                    record.chat_id,
                    record.thread_id,
                    record.auto_reply,
                ),
            )
            await db.commit()

    async def delete(self, **kwargs) -> None:
        if "chat_id" not in kwargs:
            raise ValueError("Chat ID is required for deletion")

        chat_id = kwargs["chat_id"]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM chat_history WHERE chat_id = ?
                """,
                (chat_id,),
            )
            await db.commit()

    async def get(self, **kwargs) -> Optional[ChatHistory]:
        if "chat_id" not in kwargs:
            raise ValueError("Chat ID is required")

        chat_id = kwargs["chat_id"]
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT chat_id, thread_id, auto_reply, chat_history FROM chat_history WHERE chat_id = ?
                """,
                (chat_id,),
            )
            row = await cursor.fetchone()
            if row:
                return ChatHistory(
                    chat_id=row[0],
                    thread_id=row[1],
                    auto_reply=row[2],
                    history=row[3] if row[3] else None,
                )
        return None

    async def get_all(self) -> List[ChatHistory]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT chat_id, thread_id, auto_reply FROM chat_history
                """
            )
            rows = await cursor.fetchall()
            return [
                ChatHistory(
                    chat_id=row[0],
                    thread_id=row[1],
                    auto_reply=row[2],
                )
                for row in rows
            ]

    async def clear_thread_id(self, chat_id: int) -> None:
        """
        Clear the thread ID for a chat.

        Args:
            chat_id: The ID of the chat
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE chat_history SET thread_id = NULL WHERE chat_id = ?
                """,
                (chat_id,),
            )
            await db.commit()

    async def set_auto_reply(self, chat_id: int, auto_reply: bool) -> None:
        """
        Set the auto-reply flag for a chat.

        Args:
            chat_id: The ID of the chat
            auto_reply: The auto-reply flag
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE chat_history SET auto_reply = ? WHERE chat_id = ?
                """,
                (auto_reply, chat_id),
            )
            await db.commit()


class TelegramSqliteUserData(UserData):
    """
    Implementation of the UserData interface using SQLite tables.
    """

    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path)
        self.authorised_chats_table = AuthorisedChatsTable(self.db_path)
        self.authorised_users_table = AuthorisedUsersTable(self.db_path)
        self.superusers_table = SuperusersTable(self.db_path)
        self.chat_history_table = ChatHistoryTable(self.db_path)

    async def create_db(self):
        """
        Create all tables if they don't exist.
        """
        await self.authorised_chats_table.create_table()
        await self.authorised_users_table.create_table()
        await self.superusers_table.create_table()
        await self.chat_history_table.create_table()

    async def get_chat_history(self, chat_id: int) -> ChatHistoryInterface:
        """
        Get chat history for a chat.

        Args:
            chat_id: The ID of the chat

        Returns:
            The chat history
        """
        chat_history = await self.chat_history_table.get(chat_id=chat_id)
        if chat_history:
            return ChatHistoryInterface(
                chat_id=chat_history.chat_id,
                thread_id=chat_history.thread_id,
                auto_reply=chat_history.auto_reply,
                chat_history=json.loads(chat_history.history)
                if chat_history.history
                else [],
            )

        # Create a new chat history record
        new_chat_history = ChatHistory(
            chat_id=chat_id,
            thread_id=None,
            auto_reply=True,
            history=json.dumps([]),  # Initialize with empty history
        )
        await self.chat_history_table.insert(new_chat_history)
        return ChatHistoryInterface(
            chat_id=chat_id,
            thread_id=None,
            auto_reply=True,
            chat_history=[],
        )

    async def save_chat_history(self, history: ChatHistoryInterface):
        """
        Save chat history.

        Args:
            history: The chat history to save
        """
        chat_history = ChatHistory(
            chat_id=history.chat_id,
            thread_id=history.thread_id,
            auto_reply=history.auto_reply,
            history=json.dumps(history.chat_history) if history.chat_history else "[]",
        )
        await self.chat_history_table.update(chat_history)

    async def check_user_authorised(self, user_id: int):
        """
        Check if a user is authorised.

        Args:
            user_id: The ID of the user

        Returns:
            True if the user is authorised

        Raises:
            NotAuthorised: If the user is not authorised
        """
        user = await self.authorised_users_table.get(user_id=user_id)
        if user:
            return True
        raise NotAuthorised(str(user_id))

    async def check_superuser(self, user_id: int):
        """
        Check if a user is a superuser.

        Args:
            user_id: The ID of the user

        Returns:
            True if the user is a superuser

        Raises:
            NotAuthorised: If the user is not a superuser
        """
        superuser = await self.superusers_table.get(user_id=user_id)
        if superuser:
            return True
        raise NotAuthorised(str(user_id))

    async def check_chat_authorised(self, chat_id: int):
        """
        Check if a chat is authorised.

        Args:
            chat_id: The ID of the chat

        Returns:
            True if the chat is authorised

        Raises:
            NotAuthorised: If the chat is not authorised
        """
        chat = await self.authorised_chats_table.get(chat_id=chat_id)
        if chat:
            return True
        raise NotAuthorised(str(chat_id))

    async def authorise_user(self, user_id: int):
        """
        Authorise a user.

        Args:
            user_id: The ID of the user
        """
        user = AuthorisedUser(user_id=user_id)
        await self.authorised_users_table.insert(user)

    async def promote_superuser(self, user_id: int):
        """
        Promote a user to superuser.

        Args:
            user_id: The ID of the user
        """
        await self.authorise_user(user_id)
        superuser = Superuser(user_id=user_id)
        await self.superusers_table.insert(superuser)

    async def demote_superuser(self, user_id: int):
        """
        Demote a superuser.

        Args:
            user_id: The ID of the user
        """
        await self.superusers_table.delete(user_id=user_id)

    async def authorise_chat(self, chat_id: int):
        """
        Authorise a chat.

        Args:
            chat_id: The ID of the chat
        """
        chat = AuthorisedChat(chat_id=chat_id)
        await self.authorised_chats_table.insert(chat)

    async def deauthorise_user(self, user_id: int):
        """
        Deauthorise a user.

        Args:
            user_id: The ID of the user
        """
        await self.authorised_users_table.delete(user_id=user_id)

    async def deauthorise_chat(self, chat_id: int):
        """
        Deauthorise a chat.

        Args:
            chat_id: The ID of the chat
        """
        await self.authorised_chats_table.delete(chat_id=chat_id)

    async def clear_last_thread_id(self, chat_id: int):
        """
        Clear the last thread ID for a chat.

        Args:
            chat_id: The ID of the chat
        """
        await self.chat_history_table.clear_thread_id(chat_id)

    async def set_auto_reply(self, chat_id: int, auto_reply: bool):
        """
        Set the auto-reply flag for a chat.

        Args:
            chat_id: The ID of the chat
            auto_reply: The auto-reply flag
        """
        await self.chat_history_table.set_auto_reply(chat_id, auto_reply)


# Create a singleton instance
def get_telegram_data() -> TelegramSqliteUserData:
    """
    Get the singleton instance of TelegramSqliteUserData.

    Returns:
        TelegramSqliteUserData: The singleton instance.
    """
    return TelegramSqliteUserData()


# Add to assistants/user_data/sqlite_backend/telegram_chat_data.py


class BotConversationMessage(BaseModel):
    """
    Pydantic model representing a message in a multi-bot conversation.

    Attributes:
        id: Optional[int]: Auto-incremented message ID
        chat_id (int): The chat ID where the message was sent
        bot_id (str): The bot identifier ("user" for user messages)
        user_id (int): The user ID (bot ID for bot messages)
        text (str): The message content
        timestamp (float): When the message was sent
    """

    id: Optional[int] = None
    chat_id: int
    bot_id: str  # "user" for user messages, bot identifier for bot messages
    user_id: int
    text: str
    timestamp: float


class BotConversationsTable(Table[BotConversationMessage]):
    """Table for multi-bot conversation messages."""

    def get_table_name(self) -> str:
        return "bot_conversations"

    def get_model_class(self):
        return BotConversationMessage

    def get_create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS bot_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                bot_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """

    async def migrate_if_needed(self) -> None:
        # No migrations needed for new table
        pass

    async def insert(self, record: BotConversationMessage) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO bot_conversations 
                (chat_id, bot_id, user_id, text, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.chat_id,
                    record.bot_id,
                    record.user_id,
                    record.text,
                    record.timestamp,
                ),
            )
            await db.commit()
            record.id = cursor.lastrowid

    async def update(self, record: BotConversationMessage) -> None:
        pass

    async def delete(self, **kwargs) -> None:
        pass

    async def get(self, **kwargs) -> Optional[BotConversationMessage]:
        pass

    async def get_all(self) -> List[BotConversationMessage]:
        pass

    async def get_chat_messages(
        self, chat_id: int, limit: int = 100
    ) -> List[BotConversationMessage]:
        """Get messages for a specific chat, ordered by timestamp."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, chat_id, bot_id, user_id, text, timestamp 
                FROM bot_conversations
                WHERE chat_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (chat_id, limit),
            )
            rows = await cursor.fetchall()
            return [
                BotConversationMessage(
                    id=row[0],
                    chat_id=row[1],
                    bot_id=row[2],
                    user_id=row[3],
                    text=row[4],
                    timestamp=row[5],
                )
                for row in rows
            ]

    async def get_messages_since_last_bot_response(
        self, chat_id: int, bot_id: str, limit: int = 100
    ) -> List[BotConversationMessage]:
        """Get all messages since the last response from the specified bot."""
        async with aiosqlite.connect(self.db_path) as db:
            # First, find the timestamp of the bot's last message
            cursor = await db.execute(
                """
                SELECT MAX(timestamp) 
                FROM bot_conversations
                WHERE chat_id = ? AND bot_id = ?
                """,
                (chat_id, bot_id),
            )
            row = await cursor.fetchone()
            if not row or not row[0]:
                # If the bot hasn't sent any messages yet, get all messages
                return await self.get_chat_messages(chat_id, limit)

            last_response_time = row[0]

            # Now get all messages after that timestamp
            cursor = await db.execute(
                """
                SELECT id, chat_id, bot_id, user_id, text, timestamp 
                FROM bot_conversations
                WHERE chat_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (chat_id, last_response_time, limit),
            )
            rows = await cursor.fetchall()
            return [
                BotConversationMessage(
                    id=row[0],
                    chat_id=row[1],
                    bot_id=row[2],
                    user_id=row[3],
                    text=row[4],
                    timestamp=row[5],
                )
                for row in rows
            ]

    async def get_last_message(self, chat_id: int) -> Optional[BotConversationMessage]:
        """Get the most recent message for a chat."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, chat_id, bot_id, user_id, text, timestamp 
                FROM bot_conversations
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (chat_id,),
            )
            row = await cursor.fetchone()
            if row:
                return BotConversationMessage(
                    id=row[0],
                    chat_id=row[1],
                    bot_id=row[2],
                    user_id=row[3],
                    text=row[4],
                    timestamp=row[5],
                )
            return None
