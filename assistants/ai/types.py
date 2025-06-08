"""
This module defines the types used by the generic assistants API.
These components are used to represent and manage message data and interactions
with assistant classes.

Classes:
    - MessageData: Data class representing message data.
    - AssistantProtocol: Protocol defining the interface for assistant classes.
    - MessageDict: Typed dictionary for message data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Literal, NotRequired, Optional, TypedDict

ThinkingLevel = Literal[0, 1, 2]


@dataclass
class ThinkingConfig:
    level: ThinkingLevel
    type: Literal["enabled", "disabled"] = "enabled"
    budget_tokens: Optional[int] = None

    @classmethod
    def get_thinking_config(
        cls, level: ThinkingLevel = 0, max_tokens: Optional[int] = None
    ) -> "ThinkingConfig":
        """
        Get a ThinkingConfig instance with the specified level and budget tokens.

        :param level: The thinking level (0, 1, or 2).
        :param max_tokens: Optional max response tokens (will be used to calculate thinking budget).
        :return: An instance of ThinkingConfig.
        """
        return cls(
            level=level,
            budget_tokens=(max_tokens // 4) * 3 if level > 0 and max_tokens else None,
        )

    def __bool__(self):
        """
        Check if the thinking configuration is enabled.

        :return: True if the level is greater than 0, False otherwise.
        """
        return self.level > 0 and self.type == "enabled"


@dataclass
class MessageData:
    """
    Data class representing message data.

    Attributes:
        text_content (str): The text content of the message.
        thread_id (Optional[str]): The ID of the thread the message belongs to.
    """

    text_content: str
    thread_id: Optional[str] = None


class AudioMessageData(TypedDict):
    id: str


class MessageDict(TypedDict):
    """
    Typed dictionary for message data.

    Attributes:
        role (str): The role of the message sender (e.g., 'user', 'assistant').
        content (Optional[str]): The content of the message.
        audio (Optional[str]): Optional audio data associated with the message.
    """

    role: str
    content: str | None
    audio: NotRequired[AudioMessageData]


class ConversationManagementInterface(ABC):
    """Interface for conversation state management functionality."""

    @abstractmethod
    async def save_conversation_state(self) -> str:
        """Save the current conversation state."""

    @abstractmethod
    async def get_last_message(self, thread_id: str) -> Optional[MessageData]:
        """Get the last message from the conversation."""

    @abstractmethod
    async def async_get_conversation_id(self) -> str:
        """Get the conversation ID."""

    @abstractmethod
    async def get_whole_thread(self) -> list[MessageDict]:
        """Get the whole thread of messages."""


class AssistantInterface(ABC):
    """Core assistant functionality interface."""

    conversation_id = None
    memory: list[MessageDict]
    thinking: ThinkingConfig

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
        Standard initialization for all assistant interfaces.

        :param model: The model identifier to be used by the assistant
        :param api_key: API key for the service provider
        :param instructions: Optional instructions for the assistant
        :param max_history_tokens: Maximum number of tokens to retain in memory
        :param max_response_tokens: Maximum number of tokens for the response
        :param thinking: Configuration for thinking/reasoning capabilities
        :param kwargs: Additional provider-specific parameters
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the assistant."""

    @abstractmethod
    async def load_conversation(
        self,
        conversation_id: Optional[str] = None,
        initial_system_message: Optional[str] = None,
    ) -> None:
        """
        Load a conversation by ID or initialize a new one with an optional system message.
        If no conversation ID is provided, a new conversation will be created.
        """

    @property
    @abstractmethod
    def conversation_payload(self) -> list[MessageDict]:
        """
        Get the conversation payload.

        :return: List of messages in the conversation.
        """

    @abstractmethod
    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """Converse with the assistant."""

    @abstractmethod
    async def remember(self, message: MessageDict) -> None:
        """Store a message in the assistant's memory."""

    @property
    def is_reasoning_model(self) -> bool:
        """
        Check if the assistant is a reasoning model.

        :return: True if the assistant is a reasoning model, False otherwise.
        """
        return False


class StreamingAssistantInterface(AssistantInterface):
    """
    Interface for the Streaming Assistant class.
    This interface extends the AssistantInterface to include streaming capabilities.
    """

    @abstractmethod
    def _provider_stream_response(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Abstract method for provider-specific streaming logic.
        Should yield response chunks as they become available.
        """

    async def stream_converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Shared streaming logic for all assistants. Handles memory and delegates to provider.
        """
        if not user_input:
            return

        if thread_id:
            await self.load_conversation(conversation_id=thread_id)

        await self.remember(MessageDict(role="user", content=user_input))

        full_response = ""
        async for chunk in self._provider_stream_response(user_input, thread_id):
            full_response += chunk
            yield chunk

        if full_response:
            await self.remember(MessageDict(role="assistant", content=full_response))
