"""
This module provides the `MemoryMixin` class, which handles memory-related functionality for managing conversations.

Classes:
    - MemoryMixin: Mixin class to handle memory-related functionality, including remembering messages, truncating memory, and loading/saving conversations from/to a database.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from assistants.ai.types import MessageData, MessageDict
from assistants.user_data.sqlite_backend import conversations_table
from assistants.user_data.sqlite_backend.conversations import Conversation


class MemoryMixin:
    """
    Mixin class to handle memory-related functionality.
    """

    def __init__(self, max_memory: int = 50):
        """
        Initialize the MemoryMixin instance.

        :param max_memory: Maximum number of messages to retain in memory.
        """
        self.memory: list[MessageDict] = []
        self.max_memory = max_memory
        self.conversation_id = None

    def truncate_memory(self):
        """
        Truncate the memory to the maximum allowed messages.
        """
        self.memory = self.memory[-self.max_memory :]

    def remember(self, message: MessageDict):
        """
        Remember a new message.

        :param message: The message to remember.
        """
        self.truncate_memory()
        self.memory.append(message)

    async def load_conversation(self, conversation_id: Optional[str] = None):
        """
        Load the last conversation from the database.

        :param conversation_id: Optional ID of the conversation to load.
        """
        if conversation_id:
            conversation = await conversations_table.get_conversation(conversation_id)
        else:
            conversation = await conversations_table.get_last_conversation()

        self.memory = json.loads(conversation.conversation) if conversation else []
        self.conversation_id = conversation.id if conversation else uuid.uuid4().hex

    async def save_conversation_state(self) -> str:
        """
        Save the current conversation to the database.
        :return: The conversation ID.
        """
        if not self.memory:
            return

        if self.conversation_id is None:
            self.conversation_id = uuid.uuid4().hex

        await conversations_table.save_conversation(
            Conversation(
                id=self.conversation_id,
                conversation=json.dumps(self.memory),
                last_updated=datetime.now(),
            )
        )
        return self.conversation_id

    def get_last_message(self, thread_id: str) -> Optional[MessageData]:
        """
        Get the last message from the conversation or None if no message exists.
        Conversation must have already been loaded.

        :param thread_id: Not used; required by protocol
        :return: MessageData with the last message and current conversation_id.
        """
        if not self.memory:
            return None
        return MessageData(
            text_content=self.memory[-1]["content"], thread_id=self.conversation_id
        )
