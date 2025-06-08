"""
This module defines the Claude class, which encapsulates interactions with the
Anthropic API
It includes memory management functionality through the MemoryMixin class.

Classes:
    - Claude: Encapsulates interactions with the Anthropic API.
"""

from typing import AsyncIterator, Optional

from anthropic import AsyncAnthropic

from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.types import (
    AssistantInterface,
    MessageData,
    MessageDict,
    StreamingAssistantInterface,
    ThinkingConfig,
)
from assistants.config import environment
from assistants.lib.exceptions import ConfigError

INSTRUCTIONS_UNDERSTOOD = "Instructions understood."


class ClaudeAssistant(
    ConversationHistoryMixin, StreamingAssistantInterface, AssistantInterface
):
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
        api_key: Optional[str] = environment.ANTHROPIC_API_KEY,
        instructions: Optional[str] = None,
        max_history_tokens: int = environment.DEFAULT_MAX_HISTORY_TOKENS,
        max_response_tokens: int = environment.DEFAULT_MAX_RESPONSE_TOKENS,
        thinking: Optional[ThinkingConfig] = None,
        **kwargs,
    ) -> None:
        """
        Initialise the Claude instance.

        :param model: The model to be used by the assistant.
        :param api_key: API key for Anthropic. Defaults to ANTHROPIC_API_KEY.
        :param instructions: Optional instructions for the assistant.
        :param max_history_tokens: Maximum number of messages to retain in memory.
        :param max_response_tokens: Maximum number of tokens for the response.
        :param thinking: Configuration for thinking capabilities.
        :param kwargs: Additional parameters.
        :raises ConfigError: If the API key is missing.
        """
        if not api_key:
            raise ConfigError("Missing 'ANTHROPIC_API_KEY' environment variable")

        # Initialize the mixin
        ConversationHistoryMixin.__init__(self, max_history_tokens)

        # Store instance variables
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_response_tokens = max_response_tokens
        self.instructions = instructions
        self.thinking = (
            self.set_thinking_budget(thinking)
            if thinking
            else ThinkingConfig(level=0, type="enabled")
        )

    def set_thinking_budget(self, thinking: ThinkingConfig) -> ThinkingConfig:
        """
        Set the thinking budget for the assistant.

        :param thinking: Configuration for thinking capabilities.
        """
        if thinking.budget_tokens is None:
            thinking = ThinkingConfig(
                level=thinking.level,
                budget_tokens=self.max_response_tokens,
                type=thinking.type,
            )
        return thinking

    async def start(self) -> None:
        """
        Do nothing
        """

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

        if thread_id and not self.conversation_id:
            self.conversation_id = thread_id

        if thread_id and not self.memory:
            await self.load_conversation(conversation_id=thread_id)

        await self.remember({"role": "user", "content": user_input})

        max_tokens = self.max_history_tokens + self.max_response_tokens

        kwargs: dict[str, object] = {
            "max_tokens": max_tokens,
            "model": self.model,
            "messages": self._prepend_instructions(),
        }

        if self.thinking:
            kwargs["thinking"] = {
                "type": self.thinking.type,
                "budget_tokens": self.thinking.budget_tokens,
            }

        response = await self.client.messages.create(**kwargs)
        text_content = next(
            (block for block in response.content if hasattr(block, "text")), None
        )

        if not text_content:
            return None

        await self.remember({"role": "assistant", "content": text_content.text})
        return MessageData(text_content=text_content.text)

    def _prepend_instructions(self) -> list[MessageDict]:
        return [
            {"role": "user", "content": self.instructions},
            {
                "role": "assistant",
                "content": INSTRUCTIONS_UNDERSTOOD,
            },
            *self.memory,
        ]

    async def _provider_stream_response(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        response = await self.client.messages.create(
            max_tokens=self.max_response_tokens,
            model=self.model,
            messages=self.conversation_payload,
            stream=True,
        )

        async for chunk in response:
            if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                yield chunk.delta.text

    @property
    def is_reasoning_model(self):
        return True

    @property
    def conversation_payload(self) -> list[MessageDict]:
        """
        Get the conversation payload for the assistant.

        :return: The conversation payload.
        """
        return self._prepend_instructions()
