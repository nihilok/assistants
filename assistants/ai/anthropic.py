"""
This module defines the Claude class, which encapsulates interactions with the
Anthropic API
It includes memory management functionality through the MemoryMixin class.

Classes:
    - Claude: Encapsulates interactions with the Anthropic API.
"""

from typing import Optional

from assistants.ai.memory import MemoryMixin
from assistants.ai.types import MessageData
from assistants.config import environment
from assistants.lib.exceptions import ConfigError

from anthropic import AsyncAnthropic

INSTRUCTIONS_UNDERSTOOD = "Instructions understood."


class Claude(MemoryMixin):
    """
    Claude class encapsulates interactions with the Anthropic API.

    Inherits from:
        - AssistantProtocol: Protocol defining the interface for assistant classes.
        - MemoryMixin: Mixin class to handle memory-related functionality.

    Attributes:
        model (str): The model to be used by the assistant.
        max_tokens (int): Maximum number of tokens for the response.
        max_memory (int): Maximum number of messages to retain in memory.
        client (AsyncAnthropic): Client for interacting with the Anthropic API.
    """

    def __init__(
        self,
        model: str,
        instructions: Optional[str] = None,
        max_tokens: int = environment.CLAUDE_MAX_TOKENS,
        max_memory: int = 50,
        api_key: Optional[str] = environment.ANTHROPIC_API_KEY,
    ) -> None:
        """
        Initialize the Claude instance.

        :param model: The model to be used by the assistant.
        :param max_tokens: Maximum number of tokens for the response.
        :param max_memory: Maximum number of messages to retain in memory.
        :param api_key: API key for Anthropic. Defaults to ANTHROPIC_API_KEY.
        :raises ConfigError: If the API key is missing.
        """
        if not api_key:
            raise ConfigError("Missing 'ANTHROPIC_API_KEY' environment variable")

        MemoryMixin.__init__(self, max_memory)
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.instructions = instructions

    async def start(self) -> None:
        """
        Load the conversation instance.
        """
        await self.load_conversation()

    async def load_conversation(self, conversation_id: Optional[str] = None):
        """
        Load the conversation from the database.
        Also adds the instructions to the memory if provided and not
        already present, or not the most recent instructions.

        :param conversation_id: Optional ID of the conversation to load.
        """
        await super().load_conversation(conversation_id)
        if self.instructions:
            # Check if the instructions are already in memory
            for idx, message in enumerate(self.memory):
                if (
                    message.get("role") == "user"
                    and message.get("content") == self.instructions
                ):
                    understood_count = sum(
                        1
                        for msg in self.memory[idx + 1 :]
                        if msg.get("role") == "assistant"
                        and msg.get("content") == INSTRUCTIONS_UNDERSTOOD
                    )
                    if understood_count < 2:
                        # Most recent instructions are equivalent to the current ones
                        return

            self.memory = [
                *self.memory,
                {"role": "user", "content": self.instructions},
                {"role": "assistant", "content": INSTRUCTIONS_UNDERSTOOD},
            ]

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """
        Converse with the assistant by creating or continuing a thread.

        :param user_input: The user's input message.
        :param thread_id: Optional ID of the thread to continue.
        :return: The last message in the thread.
        """
        if not user_input:
            return None

        self.remember({"role": "user", "content": user_input})
        response = await self.client.messages.create(
            max_tokens=self.max_tokens, model=self.model, messages=self.memory
        )
        self.remember({"role": "assistant", "content": response.content[0].text})
        return MessageData(text_content=response.content[0].text)
