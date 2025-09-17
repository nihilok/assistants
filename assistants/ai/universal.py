"""
Universal Assistant implementation using the univllm library.

This module provides a unified interface for multiple LLM providers through
the univllm package, replacing the legacy provider-specific implementations.

Classes:
    - UniversalAssistant: Unified assistant class supporting multiple providers
"""

import warnings
from typing import AsyncIterator, Optional, Sequence

from univllm import UniversalLLMClient, is_unsupported_model
from univllm.models import Message

from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.types import (
    AssistantInterface,
    MessageData,
    MessageDict,
    MessageInput,
    StreamingAssistantInterface,
    ThinkingConfig,
)
from assistants.lib.exceptions import ConfigError


class UniversalAssistant(
    ConversationHistoryMixin, StreamingAssistantInterface, AssistantInterface
):
    """
    Universal Assistant class that uses the univllm library for LLM interactions.

    This class provides a unified interface for multiple LLM providers including
    OpenAI, Anthropic, Deepseek, and Mistral through the univllm package.

    Attributes:
        model (str): The model to be used by the assistant.
        client (UniversalLLMClient): Universal client for LLM interactions.
        instructions (Optional[str]): Instructions for the assistant.
        max_response_tokens (int): Maximum number of tokens for the response.
        thinking (Optional[ThinkingConfig]): Configuration for thinking capabilities.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        instructions: Optional[str] = None,
        max_history_tokens: int = 0,
        max_response_tokens: int = 0,
        thinking: Optional[ThinkingConfig] = None,
        **kwargs,
    ) -> None:
        """
        Initialize the UniversalAssistant instance.

        :param model: The model to be used by the assistant.
        :param api_key: API key for the provider (optional, can use env vars).
        :param instructions: Optional instructions for the assistant.
        :param max_history_tokens: Maximum number of tokens to retain in memory.
        :param max_response_tokens: Maximum number of tokens for the response.
        :param thinking: Configuration for thinking capabilities.
        :param kwargs: Additional parameters.
        """
        if is_unsupported_model(model):
            raise ConfigError(f"The model '{model}' is not supported by univllm.")

        # Initialize the mixin
        ConversationHistoryMixin.__init__(self, max_history_tokens)

        # Store instance variables
        self.model = model
        self.instructions = instructions
        self.max_response_tokens = max_response_tokens
        self.thinking = thinking or ThinkingConfig(level=0, type="enabled")

        # Initialize the universal client
        try:
            if api_key:
                # Provider will be auto-detected from model name
                self.client = UniversalLLMClient(api_key=api_key)
            else:
                # Use environment variables for API keys
                self.client = UniversalLLMClient()
        except Exception as e:
            raise ConfigError(f"Failed to initialize UniversalLLMClient: {e}") from e

    async def start(self) -> None:
        """
        Initialize the message history with system instructions if provided.
        """
        if self.instructions and not self.memory:
            self.memory = [{"role": "system", "content": self.instructions}]

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """
        Converse with the assistant using the universal client.

        :param user_input: The user's input message.
        :param thread_id: Optional thread ID for conversation context.
        :return: MessageData containing the assistant's response.
        """
        if thread_id and not self.memory:
            await self.load_conversation(conversation_id=thread_id)

        # Add user message to memory
        await self.remember(MessageDict(role="user", content=user_input))

        # Convert memory to univllm format
        messages = self._convert_memory_to_univllm_format()

        try:
            # Get response from universal client using correct method signature
            response = await self.client.complete(
                messages=messages,
                model=self.model,
                max_tokens=self.max_response_tokens
                if self.max_response_tokens > 0
                else None,
            )

            # Store assistant's response in memory
            await self.remember(MessageDict(role="assistant", content=response.content))

            return MessageData(
                text_content=str(response.content),
                thread_id=thread_id,
            )

        except Exception as e:
            raise ConfigError(f"Failed to get completion: {e}") from e

    async def _provider_stream_response(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Provider-specific streaming logic using the universal client.

        :param user_input: The user's input message.
        :param thread_id: Optional thread ID for conversation context.
        :yield: Response chunks as they become available.
        """
        # Convert memory to univllm format
        messages = self._convert_memory_to_univllm_format()
        max_tokens = self.max_response_tokens if self.max_response_tokens > 0 else None

        try:
            # Stream response from universal client
            async for chunk in self.client.stream_complete(
                messages=messages, model=self.model, max_tokens=max_tokens
            ):
                yield chunk

        except Exception as e:
            raise ConfigError(f"Failed to get streaming completion: {e}") from e

    def _convert_memory_to_univllm_format(self) -> list[Message]:
        """
        Convert internal memory format to univllm Message format.

        :return: List of Message objects for univllm.
        """
        messages = []
        for msg in self.memory:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append(Message(role=msg["role"], content=msg["content"]))
        return messages

    @property
    def conversation_payload(self) -> Sequence[MessageInput]:
        """
        Get the conversation payload.

        :return: List of messages in the conversation.
        """
        return self.memory

    async def load_conversation(self, conversation_id: Optional[str] = None) -> None:
        """
        Load a conversation by ID or initialize a new one.

        :param conversation_id: The ID of the conversation to load.
        """
        if conversation_id:
            self.conversation_id = conversation_id
            # Load conversation from database/storage
            # This delegates to the ConversationHistoryMixin
            await self._load_conversation_from_storage(conversation_id)
        else:
            # Initialize new conversation
            self.conversation_id = None
            self.memory = []
            if self.instructions:
                await self.start()

    async def remember(self, *args, **kwargs) -> None:
        """
        Store a message in the assistant's memory.
        """
        # Delegate to the mixin
        await self._remember_message(*args, **kwargs)

    async def get_last_message(self, thread_id: str) -> Optional[MessageData]:
        """
        Get the last message from the conversation.

        :param thread_id: The thread ID (not used in current implementation).
        :return: MessageData with the last message or None if no messages exist.
        """
        if not self.memory:
            return None

        # Find the last assistant message
        for msg in reversed(self.memory):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                return MessageData(
                    text_content=msg.get("content", ""),
                    thread_id=self.conversation_id,
                )
        return None

    async def async_get_conversation_id(self) -> str:
        """
        Get the conversation ID asynchronously.

        :return: The conversation ID.
        """
        if not self.conversation_id:
            # Generate or load conversation ID
            self.conversation_id = await self._generate_conversation_id()
        return self.conversation_id

    async def _load_conversation_from_storage(self, conversation_id: str) -> None:
        """
        Load conversation from storage (placeholder for actual implementation).

        :param conversation_id: The ID of the conversation to load.
        """
        # This would typically load from database
        # For now, delegate to parent class if it has the functionality
        pass

    async def _remember_message(self, message: MessageDict) -> None:
        """
        Store a message in memory (placeholder for actual implementation).

        :param message: The message to store.
        """
        # Add to memory
        self.memory.append(message)

        # Optionally persist to storage
        if self.conversation_id:
            await self._persist_message_to_storage(message)

    async def _persist_message_to_storage(self, message: MessageDict) -> None:
        """
        Persist message to storage (placeholder for actual implementation).

        :param message: The message to persist.
        """
        # This would typically save to database
        pass

    async def _generate_conversation_id(self) -> str:
        """
        Generate a new conversation ID.

        :return: A new conversation ID.
        """
        import uuid

        return str(uuid.uuid4())


# Convenience function for backward compatibility
def create_universal_assistant(
    model: str, provider: Optional[str] = None, **kwargs
) -> UniversalAssistant:
    """
    Create a UniversalAssistant instance with optional provider specification.

    :param model: The model to use.
    :param provider: Optional provider name (auto-detected from model if not provided).
    :param kwargs: Additional arguments for the assistant.
    :return: UniversalAssistant instance.
    """
    if provider:
        warnings.warn(
            "Provider parameter is deprecated. Provider is auto-detected from model name.",
            DeprecationWarning,
            stacklevel=2,
        )

    return UniversalAssistant(model=model, **kwargs)
