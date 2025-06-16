"""
This module defines the `Conversation` data class and the `ConversationsTable` class for managing conversation records in an SQLite database.

Classes:
    - Conversation: Pydantic model representing a conversation record.
    - ConversationsTable: Class for interacting with the conversations table in the SQLite database.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Optional

import aiosqlite
from pydantic import BaseModel

from assistants.user_data.sqlite_backend.message import Message
from assistants.user_data.sqlite_backend.table import Table


class Conversation(BaseModel):
    """
    Pydantic model representing a conversation record.

    Attributes:
        id (str): The unique identifier of the conversation.
        last_updated (datetime): The timestamp of the last update to the conversation.
    """

    id: str
    last_updated: datetime

    async def save(self) -> None:
        """
        Insert or update the conversation record in the database.

        Returns:
            The saved Conversation object.
        """
        await get_conversations_table().insert(self)


class ConversationsTable(Table[Conversation]):
    """
    Class for interacting with the conversations table in the SQLite database.
    """

    def get_table_name(self) -> str:
        """
        Get the name of the table.

        Returns:
            The name of the table
        """
        return "conversations"

    def get_model_class(self):
        """
        Get the Pydantic model class for the table records.

        Returns:
            The Pydantic model class
        """
        return Conversation

    def get_create_table_sql(self) -> str:
        """
        Get the SQL statement for creating the table.

        Returns:
            The SQL CREATE TABLE statement
        """
        return """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                last_updated TEXT
            )
        """

    async def migrate_if_needed(self) -> None:
        """
        Perform schema migrations if needed.

        This method checks the current schema and performs migrations
        if the schema has changed.
        """
        # Convert the `conversation` field to rows in the MessageTable
        from assistants.user_data.sqlite_backend.message import MessageTable

        messages_table = MessageTable(self.db_path)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT id, conversation, last_updated FROM conversations ORDER BY last_updated DESC
                    """
                )
                try:
                    rows = await cursor.fetchall()
                except aiosqlite.OperationalError as e:
                    if "no such column" in str(e):
                        # If the column doesn't exist, we can skip migration
                        return
                    else:
                        raise e

                for row in rows:
                    messages = json.loads(row[1])
                    for message in messages:
                        message_record = Message(
                            role=message.get("role", "user"),
                            content=message.get("content", ""),
                            conversation_id=row[0],
                        )
                        await messages_table.insert(message_record)
                        await asyncio.sleep(
                            0.1
                        )  # To avoid overwhelming the database with inserts and preserve order
                    new_conversation = Conversation(
                        id=row[0],
                        last_updated=row[2],
                    )
                    await self.update(new_conversation)
        except aiosqlite.OperationalError as e:
            if "no such column" in str(e):
                # If the column doesn't exist, we can skip this step
                pass
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                ALTER TABLE conversations DROP COLUMN conversation
                """
                )
                await db.commit()
        except aiosqlite.OperationalError as e:
            if "no such column" in str(e):
                # If the column doesn't exist, we can skip this step
                pass
            else:
                raise e

    async def insert(self, record: Conversation) -> None:
        """
        Insert a conversation record into the table.

        Args:
            record: The conversation record to insert
        """
        await self.update(record)  # Same implementation as update

    async def update(self, record: Conversation) -> None:
        """
        Update a conversation record in the table.

        Args:
            record: The conversation record to update
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                REPLACE INTO conversations (id, last_updated) VALUES (?, ?)
                """,
                (
                    record.id,
                    record.last_updated.isoformat(),
                ),
            )
            await db.commit()

    async def delete(self, **kwargs) -> None:
        """
        Delete a conversation record from the table.

        Args:
            **kwargs: Key-value pairs for identifying the record to delete
        """
        if "id" not in kwargs:
            raise ValueError("Conversation ID is required for deletion")

        conversation_id = kwargs["id"]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM conversations WHERE id = ?
                """,
                (conversation_id,),
            )
            await db.commit()

    async def get(self, **kwargs) -> Optional[Conversation]:
        """
        Get a conversation record from the table.

        Args:
            **kwargs: Key-value pairs for identifying the record to get

        Returns:
            The conversation record if found, None otherwise
        """
        if "id" not in kwargs:
            raise ValueError("Conversation ID is required")

        conversation_id = kwargs["id"]
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, last_updated FROM conversations WHERE id = ?
                """,
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if row:
                return Conversation(
                    id=row[0],
                    last_updated=datetime.fromisoformat(row[1]),
                )
        return None

    async def get_all(self) -> List[Conversation]:
        """
        Get all conversation records from the table.

        Returns:
            A list of all conversation records
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, last_updated FROM conversations ORDER BY last_updated DESC
                """
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(
                    Conversation(
                        id=row[0],
                        last_updated=datetime.fromisoformat(row[1]),
                    )
                )
            return result

    async def get_last_conversation(self) -> Optional[Conversation]:
        """
        Retrieve the most recently updated conversation from the database.

        Returns:
            The most recently updated Conversation object if found, otherwise None.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, conversation, last_updated FROM conversations ORDER BY last_updated DESC LIMIT 1
                """
            )
            row = await cursor.fetchone()
            if row:
                return Conversation(
                    id=row[0],
                    last_updated=datetime.fromisoformat(row[1]),
                )
        return None


# Create a singleton instance
def get_conversations_table() -> ConversationsTable:
    """
    Get the singleton instance of ConversationsTable.

    Returns:
        An instance of ConversationsTable.
    """
    return ConversationsTable()
