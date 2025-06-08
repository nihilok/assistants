from typing import List, Optional, Self

import aiosqlite
from pydantic import BaseModel

from assistants.user_data.sqlite_backend.table import T, Table


class Message(BaseModel):
    """
    Represents a message in a conversation.
    """

    role: str
    content: str
    conversation_id: Optional[str] = None
    timestamp: Optional[int] = None

    def __str__(self):
        return f"{self.role.title()}:\n{self.content}"

    def __repr__(self):
        return f"Message(role={self.role}, content={self.content})"

    async def save(self) -> Self:
        """
        Insert Message into the database.
        """
        await get_messages_table().insert(self)
        return self


class MessageTable(Table[Message]):
    """
    Class for interacting with the messages table in the SQLite database.
    """

    async def migrate_if_needed(self) -> None:
        pass

    async def insert(self, record: T) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "INSERT INTO messages (role, content, conversation_id) VALUES (?, ?, ?)",
                (record.role, record.content, record.conversation_id),
            ):
                await db.commit()

    async def update(self, record: T) -> None:
        pass

    async def delete(self, **kwargs) -> None:
        pass

    async def get(self, **kwargs) -> Optional[T]:
        pass

    async def get_all(self) -> List[T]:
        pass

    async def get_by_conversation_id(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[T]:
        """
        Get all messages for a specific conversation ID.

        Args:
            conversation_id: The ID of the conversation to filter messages by.

        Returns:
            A list of Message objects associated with the given conversation ID.
        """
        statement = "SELECT role, content, conversation_id FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC"
        if limit is not None:
            statement += " LIMIT ?"
            params = (conversation_id, limit)
        else:
            params = (conversation_id,)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(statement, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    Message(role=row[0], content=row[1], conversation_id=row[2])
                    for row in rows
                ]

    def get_table_name(self) -> str:
        return "messages"

    def get_model_class(self):
        return Message

    def get_create_table_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            conversation_id TEXT,
            timestamp INTEGER DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
        """


async def create_message(
    role: str, content: str, conversation_id: Optional[str] = None
) -> Message:
    """
    Create a new message and insert it into the database.

    Args:
        role: The role of the message sender (e.g., 'user', 'assistant').
        content: The content of the message.
        conversation_id: The ID of the conversation this message belongs to.

    Returns:
        The created Message object.
    """
    message = Message(role=role, content=content, conversation_id=conversation_id)
    await get_messages_table().insert(message)
    return message


def get_messages_table() -> MessageTable:
    """
    Get the messages table instance.

    Returns:
        The MessageTable instance.
    """
    return MessageTable()
