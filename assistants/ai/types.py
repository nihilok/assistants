"""
This module defines the types used by the generic assistants API.
These components are used to represent and manage message data and interactions with assistant classes.

Classes:
    - MessageData: Data class representing message data.
    - AssistantProtocol: Protocol defining the interface for assistant classes.
    - MessageDict: Typed dictionary for message data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Protocol, TypedDict


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


class MessageDict(TypedDict):
    """
    Typed dictionary for message data.

    Attributes:
        role (str): The role of the message sender (e.g., 'user', 'assistant').
        content (Optional[str]): The content of the message.
    """

    role: str
    content: str | None


class AssistantInterface(ABC):
    """
    Interface for the Assistant class.
    This interface defines the methods that must be implemented by any Assistant class.
    """

    @abstractmethod
    async def start(self) -> None:
        """
        Start the assistant.
        This method should be overridden by subclasses to implement the specific startup logic.
        """
        pass

    @abstractmethod
    async def save_conversation_state(self) -> str:
        """
        Save the current conversation state.
        This method should be overridden by subclasses to implement the specific logic for saving the conversation state.
        """
        pass

    @abstractmethod
    async def get_last_message(self, thread_id: str) -> Optional[MessageData]:
        """
        Get the last message from the conversation.
        This method should be overridden by subclasses to implement the specific logic for getting the last message.
        """
        pass

    @abstractmethod
    async def async_get_conversation_id(self) -> str:
        """
        Get the conversation ID.
        This method should be overridden by subclasses to implement the specific logic for getting the conversation ID.
        """
        pass

    @abstractmethod
    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """
        Converse with the assistant.
        This method should be overridden by subclasses to implement the specific logic for conversing with the assistant.
        """
        pass
