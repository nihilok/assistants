"""
Dummy Assistant
"""

from typing import Optional

from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.types import MessageData


class DummyAssistant(ConversationHistoryMixin):
    """
    DummyAssistant class encapsulates interactions with the Dummy API.

    Inherits from:
        - MemoryMixin: Mixin class to handle memory-related functionality.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialise the DummyAssistant instance.
        """
        ConversationHistoryMixin.__init__(self, 1)

    async def start(self):
        """
        Load the completion instance.
        """
        await self.load_conversation()

    @staticmethod
    async def converse(
        user_input: str,
        *args,
        **kwargs,  # pylint: disable=unused-argument
    ) -> Optional[MessageData]:
        """
        Converse with the assistant using the chat completion API.

        :param user_input: The user's input message.
        :return: The completion message.
        """
        if not user_input:
            return None

        message = f"Response to ```\n{user_input}\n```"
        return MessageData(text_content=message)
