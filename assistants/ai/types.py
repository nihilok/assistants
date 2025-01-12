"""
This module defines the types used by the generic assistants API.
These components are used to represent and manage message data and interactions with assistant classes.

Classes:
    - MessageData: Data class representing message data.
    - AssistantProtocol: Protocol defining the interface for assistant classes.
    - MessageDict: Typed dictionary for message data.
"""

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


class AssistantProtocol(Protocol):
    """
    Protocol defining the interface for assistant classes.

    Attributes:
        assistant_id (Optional[str]): The ID of the assistant.
    """

    assistant_id: Optional[str]

    async def start(self) -> None:
        """
        Load the assistant etc. (async init if needed).
        """
        ...

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """
        Converse with the assistant.

        :param user_input: The user's input message.
        :param thread_id: Optional ID of the thread to continue.
        :return: The last message in the thread or a string response.
        """
        ...

    def get_last_message(self, thread_id: str) -> Optional[MessageData]:
        """
        Get the last message in the thread.

        :param thread_id: the ID of the thread to continue.
        :return: last message in the thread if one exists.
        """
        ...

    def save_conversation_state(self) -> str:
        """
        Save the current state of the conversation.
        :return: The conversation ID/ Thread ID.
        """
        ...


class MessageDict(TypedDict):
    """
    Typed dictionary for message data.

    Attributes:
        role (str): The role of the message sender (e.g., 'user', 'assistant').
        content (Optional[str]): The content of the message.
    """

    role: str
    content: str | None
