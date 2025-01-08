"""
This module defines the `Conversation` data class and the `ConversationsTable` class for managing conversation records in an SQLite database.

Classes:
    - Conversation: Data class representing a conversation record.
    - ConversationsTable: Class for interacting with the conversations table in the SQLite database.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import aiosqlite

from assistants.config.file_management import DB_PATH


@dataclass
class Conversation:
    """
    Data class representing a conversation record.

    Attributes:
        id (str): The unique identifier of the conversation.
        conversation (str): The conversation data in JSON format.
        last_updated (datetime): The timestamp of the last update to the conversation.
    """

    id: str
    conversation: str
    last_updated: datetime


class ConversationsTable:
    """
    Class for interacting with the conversations table in the SQLite database.

    Attributes:
        db_path (str): The path to the SQLite database file.
    """

    def __init__(self, db_path: str):
        """
        Initialize the ConversationsTable instance.

        :param db_path: The path to the SQLite database file.
        """
        self.db_path = db_path

    async def create_table(self):
        """
        Create the conversations table if it does not exist.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    conversation TEXT,
                    last_updated TEXT
                )
            """
            )
            await db.commit()

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by its ID.

        :param conversation_id: The unique identifier of the conversation.
        :return: The Conversation object if found, otherwise None.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, conversation, last_updated FROM conversations WHERE id = ?
            """,
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if row:
                return Conversation(
                    id=row[0],
                    conversation=row[1],
                    last_updated=datetime.fromisoformat(row[2]),
                )

    async def save_conversation(self, conversation: Conversation):
        """
        Save a conversation to the database.

        :param conversation: The Conversation object to save.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                REPLACE INTO conversations (id, conversation, last_updated) VALUES (?, ?, ?)
            """,
                (
                    conversation.id,
                    conversation.conversation,
                    conversation.last_updated.isoformat(),
                ),
            )
            await db.commit()

    async def delete_conversation(self, conversation_id: str):
        """
        Delete a conversation from the database by its ID.

        :param conversation_id: The unique identifier of the conversation to delete.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM conversations WHERE id = ?
            """,
                (conversation_id,),
            )
            await db.commit()

    async def get_all_conversations(self) -> list[Conversation]:
        """
        Retrieve all conversations from the database.

        :return: A list of Conversation objects.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, conversation, last_updated FROM conversations ORDER BY last_updated DESC
            """
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                result.append(
                    Conversation(
                        id=row[0],
                        conversation=row[1],
                        last_updated=datetime.fromisoformat(row[2]),
                    )
                )
            return result

    async def get_last_conversation(self) -> Optional[Conversation]:
        """
        Retrieve the most recently updated conversation from the database.

        :return: The most recently updated Conversation object if found, otherwise None.
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
                    conversation=row[1],
                    last_updated=datetime.fromisoformat(row[2]),
                )


conversations_table = ConversationsTable(DB_PATH)
