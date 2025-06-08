from typing import Optional

from mistralai import Mistral

from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.types import (
    AssistantInterface,
    MessageData,
    MessageDict,
    ThinkingConfig,
)
from assistants.config import environment
from assistants.lib.exceptions import ConfigError


class MistralAssistant(ConversationHistoryMixin, AssistantInterface):
    """
    Mistral class encapsulates interactions with the Mistral API.

    Inherits from:
        - AssistantInterface: Interface defining the methods for assistant classes.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = environment.MISTRAL_API_KEY,
        instructions: Optional[str] = None,
        max_history_tokens: int = environment.DEFAULT_MAX_HISTORY_TOKENS,
        max_response_tokens: int = environment.DEFAULT_MAX_RESPONSE_TOKENS,
        thinking: Optional[ThinkingConfig] = None,
        **kwargs,
    ) -> None:
        """
        Initialise the Mistral instance.

        :param model: The model to be used by the assistant.
        :param api_key: API key for Mistral. Defaults to environment variable if not provided.
        :param instructions: Optional instructions for the assistant (not used by Mistral).
        :param max_history_tokens: Maximum number of tokens to retain in memory.
        :param max_response_tokens: Maximum number of tokens for the response.
        :param thinking: Configuration for thinking capabilities (not used by Mistral).
        :param kwargs: Additional parameters.
        """
        if not api_key:
            raise ConfigError("Missing 'MISTRAL_API_KEY' environment variable")

        self.model = model
        self.api_key = api_key
        self.max_response_tokens = max_response_tokens
        # Mistral doesn't use instructions or thinking, but we store them for interface compatibility
        self.instructions = instructions
        self.thinking = thinking
        ConversationHistoryMixin.__init__(self, max_history_tokens)

    async def start(self) -> None:
        pass

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        if thread_id and not self.memory:
            await self.load_conversation(
                conversation_id=thread_id,
            )
        async with Mistral(
            api_key=self.api_key,
        ) as mistral:
            await self.remember(MessageDict(role="user", content=user_input))
            res = await mistral.chat.complete_async(
                model=self.model,
                messages=self.memory,
            )
            message_text = res.choices[0].message.content
            await self.remember(MessageDict(role="assistant", content=message_text))
            return MessageData(
                text_content=message_text,
                thread_id=thread_id,
            )

    @property
    def conversation_payload(self) -> list[MessageDict]:
        """
        Get the conversation payload.

        :return: List of messages in the conversation.
        """
        return self.memory


if __name__ == "__main__":
    import asyncio

    mistral_assistant = MistralAssistant(model="codestral-2501")
    print(
        asyncio.run(
            mistral_assistant.converse(
                "Who is the best French painter? Answer in one short sentence."
            )
        )
    )
