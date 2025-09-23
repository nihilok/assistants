"""
Universal Assistant implementation using the univllm library.

This module provides a unified interface for multiple LLM providers through
the univllm package, replacing the legacy provider-specific implementations.

Classes:
    - UniversalAssistant: Unified assistant class supporting multiple providers
"""

import warnings
from typing import AsyncIterator, Optional, Sequence, Literal

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

    It also supports image generation for providers/models that expose this
    capability (e.g. OpenAI's gpt-image-1) via the generate_image API in univllm.

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

    async def image_prompt(
        self,
        prompt: str,
        model: Literal["gpt-image-1"] = "gpt-image-1",
        quality: Literal[
            "low", "medium", "high", "auto"
        ] = "low",
        size: Literal[
            "auto",
            "1024x1024",
            "1536x1024",
            "1024x1536",
            "256x256",
            "512x512",
            "1792x1024",
            "1024x1792",
        ] = "1024x1024",
    ) -> Optional[str]:
        """Generate an image using a vision-capable model via univllm.

        This mirrors the interface of the legacy OpenAIAssistant.image_prompt but
        routes the request through the universal client. Returns the first
        image's base64 data (b64_json) if available.
        """
        try:
            response = await self.client.generate_image(
                prompt=prompt,
                model=model,
                size=size,
                response_format="b64_json",
                quality=quality,  # passed through extra_params
            )
        except Exception as e:
            raise ConfigError(f"Failed to generate image: {e}") from e

        if not response.images:
            return None
        first = response.images[0]
        return first.b64_json or None

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
        payload = self.memory
        if self.instructions:
            if payload and payload[0].get("role") == "system":
                payload[0]["content"] = self.instructions
            else:
                payload = [{"role": "system", "content": self.instructions}] + payload
        return payload

    async def load_conversation(self, conversation_id: Optional[str] = None) -> None:
        """
        Load a conversation by ID or initialize a new one.

        :param conversation_id: The ID of the conversation to load.
        """
        await super().load_conversation(conversation_id)

    async def get_last_message(self) -> Optional[MessageData]:
        """
        Get the last message from the conversation.

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
