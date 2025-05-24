"""
This module provides the `MemoryMixin` class, which handles memory-related functionality
for managing conversations.

Classes:
    - MemoryMixin: Mixin class to handle memory-related functionality, including remembering
        messages, truncating memory, and loading/saving conversations from/to a database.
"""

import json
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Optional
from abc import ABCMeta, abstractmethod

import tiktoken

from assistants.ai.types import MessageData, MessageDict, AssistantInterface
from assistants.config import environment
from assistants.user_data.sqlite_backend import conversations_table
from assistants.user_data.sqlite_backend.conversations import Conversation

encoding = tiktoken.encoding_for_model("gpt-4o-mini")


class ConversationHistoryMixin(AssistantInterface, metaclass=ABCMeta):
    """
    Mixin class to handle memory-related functionality.
    """

    def __init__(
        self, max_tokens: int = environment.DEFAULT_MAX_HISTORY_TOKENS
    ) -> None:
        """
        Initialize the MemoryMixin instance.

        :param max_tokens: Maximum number of messages to retain in memory.
        """
        self.memory: list[MessageDict] = []
        self.max_history_tokens = max_tokens
        self.conversation_id = None

    def truncate_memory(self):
        """
        Use the tiktoken library to truncate memory if it exceeds the maximum token limit.
        """
        while self.memory and self.max_history_tokens < self._get_token_count():
            self.memory.pop(0)

    def remember(self, message: MessageDict, audio: Optional[bool] = False):
        """
        Remember a new message.

        :param message: The message to remember.
        """
        self.truncate_memory()
        self.memory.append(message)

    async def load_conversation(
        self,
        conversation_id: Optional[str] = None,
        initial_system_message: Optional[str] = None,
    ):
        """
        Load the last conversation from the database.

        :param conversation_id: Optional ID of the conversation to load.
        :param initial_system_message: Optional initial system message to add to the conversation.
        """
        if conversation_id:
            conversation = await conversations_table.get_conversation(conversation_id)
            if not conversation:
                conversation = Conversation(
                    id=conversation_id,
                    conversation=(
                        json.dumps(
                            [{"role": "system", "content": initial_system_message}]
                        )
                        if initial_system_message
                        else "[]"
                    ),
                    last_updated=datetime.now(),
                )
        else:
            conversation = await conversations_table.get_last_conversation()

        self.memory = json.loads(conversation.conversation) if conversation else []
        self.conversation_id = conversation.id if conversation else uuid.uuid4().hex

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

        await conversations_table.save_conversation(
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
