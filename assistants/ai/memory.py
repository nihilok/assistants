"""
This module provides the `MemoryMixin` class, which handles memory-related functionality
for managing conversations.

Classes:
    - MemoryMixin: Mixin class to handle memory-related functionality, including remembering
        messages, truncating memory, and loading/saving conversations from/to a database.
"""

import json
import uuid
from abc import abstractmethod
from copy import deepcopy
from datetime import datetime
from typing import Optional

import tiktoken

from assistants.ai.types import (
    ConversationManagementInterface,
    MessageData,
    MessageDict,
)
from assistants.config import environment
from assistants.user_data.sqlite_backend.conversations import (
    Conversation,
    get_conversations_table,
)
from assistants.user_data.sqlite_backend.message import (
    Message,
    get_messages_table,
)

encoding = tiktoken.encoding_for_model("gpt-4o-mini")


class ConversationHistoryMixin(ConversationManagementInterface):
    """Implements conversation management functionality."""

    def __init__(
        self, max_tokens: int = environment.DEFAULT_MAX_HISTORY_TOKENS
    ) -> None:
        """
        Initialise the MemoryMixin instance.

        :param max_tokens: Maximum number of messages to retain in memory.
        """
        self.memory: list[MessageDict] = []
        self.max_history_tokens = max_tokens
        self.conversation_id: str | None = None

    def truncate_memory(self):
        """
        Use the tiktoken library to truncate memory if it exceeds the maximum token limit.
        """
        while (
            self.memory
            and self.max_history_tokens
            and self.max_history_tokens < self._get_token_count()
        ):
            self.memory.pop(0)

    async def remember(self, message: MessageDict, audio: Optional[bool] = False):
        """
        Remember a new message.

        :param message: The message to remember.
        """
        if self.conversation_id is None:
            conversation = Conversation(
                id=uuid.uuid4().hex,
                conversation="",  # deprecated, but kept for compatibility
                last_updated=datetime.now(),
            )
            await conversation.save()
            self.conversation_id = conversation.id

        self.memory.append(message)
        message = Message(
            role=message["role"],
            content=message["content"],
            conversation_id=self.conversation_id,
        )
        await message.save()
        self.truncate_memory()

    async def load_conversation(
        self,
        conversation_id: Optional[str] = None,
    ):
        """
        Load the last conversation from the database.

        Args:
            conversation_id: Optional ID of the conversation to load.
        """
        if conversation_id:
            await self._load_specific_conversation(conversation_id)
        else:
            await self._load_latest_conversation()

    async def _load_specific_conversation(self, conversation_id: str):
        """Load a conversation with a specific ID or create it if it doesn't exist."""
        conversation = await get_conversations_table().get(id=conversation_id)
        if not conversation:
            # Create a new conversation if it doesn't exist
            conversation = Conversation(
                id=conversation_id,
                conversation="",  # deprecated, but kept for compatibility
                last_updated=datetime.now(),
            )
            await conversation.save()
        else:
            if conversation.conversation:
                self.memory.extend(json.loads(conversation.conversation))

        messages = await get_messages_table().get_by_conversation_id(conversation_id)
        if messages:
            self._load_memory_from_messages(messages)

        self.conversation_id = conversation_id

    async def _load_latest_conversation(self):
        """Load the most recent conversation or create a new one if none exists."""
        latest = await get_conversations_table().get_last_conversation()

        if not latest:
            # Create a new conversation if none exists
            self.conversation_id = uuid.uuid4().hex
            latest = Conversation(
                id=self.conversation_id,
                conversation="",
                last_updated=datetime.now(),
            )
            await latest.save()
            self.memory = []
        else:
            self.conversation_id = latest.id

            # Try to load from the conversation JSON first
            if latest.conversation:
                self.memory = json.loads(latest.conversation)
            else:
                # Fall back to loading from the messages table
                messages = await get_messages_table().get_by_conversation_id(latest.id)
                if messages:
                    self._load_memory_from_messages(messages)
                else:
                    self.memory = []

    def _load_memory_from_messages(self, messages: list[Message]) -> None:
        """Convert database message objects to memory format."""
        self.memory.extend(
            [
                MessageDict(role=message.role, content=message.content)
                for message in messages
            ]
        )
        self.truncate_memory()

    def _convert_system_messages_to_instructions(
        self, instructions_understood_message: str
    ):
        """Convert system messages to user/assistant pairs."""
        temp_memory = []
        for message in self.memory:
            if message["role"] == "system":
                temp_memory.extend(
                    [
                        {"role": "user", "content": message["content"]},
                        {
                            "role": "assistant",
                            "content": instructions_understood_message,
                        },
                    ]
                )
            else:
                temp_memory.append(message)
        self.memory = temp_memory

    async def async_get_conversation_id(self):
        if not self.conversation_id:
            await self.load_conversation()
        return self.conversation_id

    async def save_conversation_state(self) -> Optional[str]:
        """
        Save the current conversation to the database.
        :return: The conversation ID.
        """
        if not self.memory:
            return None

        if self.conversation_id is None:
            self.conversation_id = uuid.uuid4().hex

        await get_conversations_table().update(
            Conversation(
                id=self.conversation_id,
                conversation=json.dumps(self.memory),
                last_updated=datetime.now(),
            )
        )
        return self.conversation_id

    async def get_last_message(self, thread_id: str) -> Optional[MessageData]:
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

    @abstractmethod
    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    async def get_whole_thread(self) -> list[MessageDict]:
        """
        Get the whole thread of messages.
        :return: List of messages in the thread.
        """
        return self.memory

    def _get_token_count(self):
        return len(encoding.encode(json.dumps(self.memory)))

    def clean_audio_messages(self):
        temp_memory = deepcopy(self.memory)
        for item in temp_memory:
            if "audio" in item:
                del item["audio"]
            if item["content"].startswith("[AUDIO TRANSCRIPTION] "):
                item["content"] = item["content"].replace("[AUDIO TRANSCRIPTION]: ", "")
        return temp_memory
