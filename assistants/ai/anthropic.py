"""
This module defines the Claude class, which encapsulates interactions with the
Anthropic API
It includes memory management functionality through the MemoryMixin class.

Classes:
    - Claude: Encapsulates interactions with the Anthropic API.
"""

from typing import Optional, AsyncIterator

from anthropic import AsyncAnthropic

from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.types import (
    MessageData,
    AssistantInterface,
    StreamingAssistantInterface,
)
from assistants.config import environment
from assistants.lib.exceptions import ConfigError


INSTRUCTIONS_UNDERSTOOD = "Instructions understood."


class Claude(ConversationHistoryMixin, StreamingAssistantInterface, AssistantInterface):
    """
    Claude class encapsulates interactions with the Anthropic API.

    Inherits from:
        - AssistantProtocol: Protocol defining the interface for assistant classes.
        - MemoryMixin: Mixin class to handle memory-related functionality.

    Attributes:
        model (str): The model to be used by the assistant.
        max_tokens (int): Maximum number of tokens for the response.
        max_history_tokens (int): Maximum number of messages to retain in memory.
        client (AsyncAnthropic): Client for interacting with the Anthropic API.
    """

    def __init__(
        self,
        model: str,
        instructions: Optional[str] = None,
        max_history_tokens: int = environment.DEFAULT_MAX_HISTORY_TOKENS,
        max_response_tokens: int = environment.DEFAULT_MAX_RESPONSE_TOKENS,
        api_key: Optional[str] = environment.ANTHROPIC_API_KEY,
        thinking: bool = False,
    ) -> None:
        """
        Initialise the Claude instance.

        :param model: The model to be used by the assistant.
        :param max_response_tokens: Maximum number of tokens for the response.
        :param max_history_tokens: Maximum number of messages to retain in memory.
        :param api_key: API key for Anthropic. Defaults to ANTHROPIC_API_KEY.
        :raises ConfigError: If the API key is missing.
        """
        if not api_key:
            raise ConfigError("Missing 'ANTHROPIC_API_KEY' environment variable")

        ConversationHistoryMixin.__init__(self, max_history_tokens)
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_response_tokens = max_response_tokens
        self.instructions = instructions
        self.thinking = thinking

    async def stream_converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream the assistant's response as it's generated.

        :param user_input: The user's input message
        :param thread_id: Optional thread ID to continue a conversation
        :return: An async iterator that yields response chunks as they become available
        """
        if not user_input:
            return

        # Store the user message in memory
        self.remember({"role": "user", "content": user_input})

        # Create a streaming request to the API
        response = await self.client.messages.create(
            max_tokens=self.max_response_tokens,
            model=self.model,
            messages=self.memory,
            stream=True,  # Enable streaming
        )

        # Buffer to collect the complete response
        full_response = ""

        # Stream the response chunks
        async for chunk in response:
            if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                # Extract the text chunk
                text_chunk = chunk.delta.text

                # Add to the full response
                full_response += text_chunk

                # Yield the chunk to the caller
                yield text_chunk

        # Store the complete response in memory
        self.remember({"role": "assistant", "content": full_response})

    async def start(self) -> None:
        """
        Do nothing
        """

    async def load_conversation(
        self,
        conversation_id: Optional[str] = None,
        initial_system_message: Optional[str] = None,
    ) -> None:
        """
        Load the conversation from the database.
        Also adds the instructions to the memory if provided and not
        already present, or not the most recent instructions.

        :param conversation_id: Optional ID of the conversation to load.
        """
        await super().load_conversation(conversation_id, initial_system_message)

        # replace any instances of `{"role": "system", ...}` with `{"role": "user", ...}, {"role": "assistant", "content": INSTRUCTIONS_UNDERSTOOD}`
        temp_memory = []
        for message in self.memory:
            if message["role"] == "system":
                temp_memory.extend(
                    [
                        {
                            "role": "user",
                            "content": message["content"],
                        },
                        {
                            "role": "assistant",
                            "content": INSTRUCTIONS_UNDERSTOOD,
                        },
                    ]
                )
            else:
                temp_memory.append(message)

        self.memory = temp_memory

        if self.instructions:
            # Check if the instructions are already the most recent in the memory
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
        self,
        user_input: str,
        thread_id: Optional[str] = None,  # pylint: disable=unused-argument
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

        max_tokens = self.max_history_tokens + self.max_response_tokens

        kwargs = {
            "max_tokens": max_tokens,
            "model": self.model,
            "messages": self.memory,
        }

        if self.thinking:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": (max_tokens // 4) * 3,
            }

        response = await self.client.messages.create(**kwargs)
        text_content = next(
            (block for block in response.content if hasattr(block, "text")), None
        )

        if not text_content:
            return None

        self.remember({"role": "assistant", "content": text_content.text})
        return MessageData(text_content=text_content.text)
