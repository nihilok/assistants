"""
This module defines classes for interacting with the OpenAI API(s), including memory management functionality through the MemoryMixin class.

Classes:
    - Assistant: Encapsulates interactions with the OpenAI Responses API.
    - Completion: Encapsulates interactions with the OpenAI Chat Completion API.
"""

import hashlib
from copy import deepcopy
from typing import Any, AsyncIterator, Dict, Literal, Optional, TypeGuard, Union, cast

import openai
from openai import BadRequestError
from openai._types import NOT_GIVEN, NotGiven
from openai.types.chat import ChatCompletionAudioParam, ChatCompletionMessage
from openai.types.responses import EasyInputMessageParam

from assistants.ai.constants import REASONING_MODELS
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

ThinkingLevel = Literal[0, 1, 2]
OpenAIThinkingLevel = Literal["low", "medium", "high"]

THINKING_MAP: dict[ThinkingLevel, OpenAIThinkingLevel] = {
    0: "low",
    1: "medium",
    2: "high",
}


def is_valid_thinking_level(level: int) -> TypeGuard[ThinkingLevel]:
    """
    Check if the provided thinking level is valid.

    :param level: The thinking level to check.
    :return: True if the level is valid, False otherwise.
    """
    return level in THINKING_MAP.keys()


class ReasoningModelMixin:
    """
    Mixin class to handle reasoning model initialisation.

    Attributes:
        reasoning (Optional[Dict]): Reasoning configuration for the model.
    """

    REASONING_MODELS = REASONING_MODELS

    def reasoning_model_init(self, thinking: ThinkingConfig) -> None:
        """
        Initialise the reasoning model.
        """
        if not self.is_reasoning_model:
            return

        self._set_reasoning_effort(thinking.level)

        if hasattr(self, "tools"):
            self.tools = NOT_GIVEN

    def _set_reasoning_effort(self, thinking: ThinkingLevel) -> None:
        try:
            thinking = int(thinking)
        except (ValueError, TypeError):
            raise ConfigError(
                f"Invalid thinking level: {thinking}. Must be 0, 1, or 2."
            )

        if is_valid_thinking_level(thinking):
            self.reasoning = {"effort": THINKING_MAP[thinking]}
        else:
            raise ConfigError(
                f"Invalid thinking level: {thinking}. Must be 0, 1, or 2."
            )

    @property
    def is_reasoning_model(self) -> bool:
        return self.model in self.REASONING_MODELS

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "thinking" and isinstance(value, ThinkingConfig):
            self._set_reasoning_effort(value.level)
        return super().__setattr__(name, value)


class OpenAIAssistant(
    ReasoningModelMixin,
    ConversationHistoryMixin,
    StreamingAssistantInterface,
    AssistantInterface,
):  # pylint: disable=too-many-instance-attributes
    """
    Encapsulates interactions with the OpenAI Responses API.

    Implements AssistantInterface: Interface for assistant classes.

    Attributes:
        model (str): The model to be used by the assistant.
        instructions (str): Instructions for the assistant.
        tools (list | NotGiven): Optional tools for the assistant.
        client (openai.OpenAI): Client for interacting with the OpenAI API.
        _config_hash (Optional[str]): Hash of the current configuration.
        last_message (Optional[dict]): The last message in the conversation.
        last_prompt (Optional[str]): The last prompt sent to the assistant.
        conversation_id (Optional[str]): Unique identifier for the conversation.
        reasoning (Optional[Dict]): Reasoning configuration for the model.
    """

    def __init__(
        self,
        *,
        model: str,
        api_key: str = environment.OPENAI_API_KEY,
        instructions: str,
        tools: list | NotGiven = NOT_GIVEN,
        max_history_tokens: int = 0,
        max_response_tokens: int = 0,
        thinking: Optional[ThinkingConfig] = None,
    ):
        """
        Initialise the Assistant instance.

        :param model: The model to be used by the assistant.
        :param api_key: API key for OpenAI.
        :param instructions: Instructions for the assistant.
        :param tools: Optional tools for the assistant.
        :param max_history_tokens: Maximum tokens to retain in conversation memory.
        :param max_response_tokens: Maximum number of tokens for the response.
        :param thinking: Level of reasoning effort (0=low, 1=medium, 2=high).
        """
        if not api_key:
            raise ConfigError("Missing 'OPENAI_API_KEY' environment variable")

        self.client = openai.OpenAI(api_key=api_key)
        self.instructions = instructions
        self.model = model
        self.tools = tools
        self._config_hash: Optional[str] = None
        self.last_message: Optional[dict] = None
        self.last_prompt: Optional[str] = None
        self.reasoning: Optional[Dict[str, OpenAIThinkingLevel]] = None
        self.thinking = thinking or ThinkingConfig.get_thinking_config(level=1)
        self.max_response_tokens = max_response_tokens
        ConversationHistoryMixin.__init__(self, max_tokens=max_history_tokens)
        if thinking is not None:
            self.reasoning_model_init(thinking)

    async def start(self) -> None:
        """
        Initialize the message history with system instructions.
        """
        if not self.memory:
            self.memory = [{"role": "system", "content": self.instructions}]

    @property
    def assistant_id(self) -> str:
        """
        Get a unique identifier for the assistant.

        :return: The assistant identifier.
        """
        return self.config_hash

    @property
    def config_hash(self) -> str:
        """
        A hash of the current config options to prevent regeneration of the same assistant.

        :return: The configuration hash.
        """
        if not self._config_hash:
            self._config_hash = self._generate_config_hash()
        return self._config_hash

    def _generate_config_hash(self) -> str:
        """
        Generate a hash based on the current configuration.

        :return: The generated hash.
        """
        return hashlib.sha256(
            f"{self.instructions}{self.model}{self.tools}".encode()
        ).hexdigest()

    async def prompt(self, prompt: str) -> Any:
        """
        Send a prompt to the model using the Responses API.

        :param prompt: The message content.
        :param thread_id: Optional ID of the conversation to continue.
        :return: The response object.
        """
        self.last_prompt = prompt

        self.memory = self.clean_audio_messages()

        await self.remember({"role": "user", "content": prompt})

        response = self.client.responses.create(
            model=self.model,
            input=self._prepend_instructions(),
            reasoning=self.reasoning if self.is_reasoning_model else NOT_GIVEN,
            store=True,
            max_output_tokens=self.max_response_tokens or None,
        )

        await self.remember({"role": "assistant", "content": response.output_text})

        return response

    async def image_prompt(self, prompt: str) -> Optional[str]:
        """
        Request an image to be generated using a separate image model.

        :param prompt: The image prompt.
        :return: The URL of the generated image or None if generation failed.
        """
        self.last_prompt = prompt
        response = self.client.images.generate(
            model=environment.IMAGE_MODEL,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """
        Converse with the assistant by sending a message and getting a response.

        :param user_input: The user's input message.
        :param thread_id: Optional ID of the conversation to continue.
        :return: MessageData containing the assistant's response and conversation ID.
        """
        if not user_input:
            return None

        if thread_id is not None:
            await self.load_conversation(thread_id)

        response = await self.prompt(user_input)

        # Store the assistant's response for future reference
        self.last_message = {"role": "assistant", "content": response.output_text}

        return MessageData(
            text_content=response.output_text,
            thread_id=self.conversation_id or "",
        )

    @property
    def conversation_payload(self) -> list[EasyInputMessageParam]:
        """
        Get the conversation payload with system instructions prepended.

        :return: List of messages in the conversation.
        """
        return self._prepend_instructions()

    def _prepend_instructions(self) -> list[EasyInputMessageParam]:
        """
        Prepend system instructions to the conversation memory.

        :return: List of messages with system instructions prepended.
        """
        if not self.instructions:
            return self.memory  # type: ignore

        # Check if the first message is already a system message with instructions
        if self.memory and self.memory[0].get("role") == "system":
            if self.memory[0].get("content") == self.instructions:
                # If the instructions are already set, return the memory as is
                return self.memory  # type: ignore
            else:
                # If the instructions are different, update the first message
                self.memory[0]["content"] = self.instructions
                return self.memory  # type: ignore

        return [{"role": "system", "content": self.instructions}, *self.memory]

    async def _provider_stream_response(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        conversation_payload: list[EasyInputMessageParam] = self._prepend_instructions()

        stream = self.client.responses.create(
            model=self.model,
            input=conversation_payload,
            reasoning=self.reasoning if self.is_reasoning_model else NOT_GIVEN,
            stream=True,
        )
        for event in stream:
            if event.type == "response.output_text.delta":
                if event.delta:
                    yield event.delta


class OpenAICompletion(
    ReasoningModelMixin, ConversationHistoryMixin, AssistantInterface
):
    """
    Encapsulates interactions with the OpenAI Chat Completion API.

    Inherits from:
        - MemoryMixin: Mixin class to handle memory-related functionality.
        - AssistantInterface: Interface for assistant classes.

    Attributes:
        model (str): The model to be used for completions.
        client (openai.OpenAI): Client for interacting with the OpenAI API.
        reasoning (Optional[OpenAIThinkingLevel]): Reasoning effort for the model.
    """

    REASONING_MODELS = REASONING_MODELS

    def __init__(
        self,
        model: str,
        max_tokens: int = 4096,
        api_key: str = environment.OPENAI_API_KEY,
        thinking: Optional[ThinkingConfig] = None,
    ):
        """
        Initialize the Completion instance.

        :param model: The model to be used for completions.
        :param max_tokens: Maximum number of messages to retain in memory.
        :param api_key: API key for OpenAI.
        :param thinking: Level of reasoning effort (0=low, 1=medium, 2=high).
        """
        if not api_key:
            raise ConfigError("Missing 'OPENAI_API_KEY' environment variable")

        ConversationHistoryMixin.__init__(self, max_tokens)
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.reasoning = None
        self.thinking = thinking or ThinkingConfig.get_thinking_config(level=1)
        self.reasoning_model_init(self.thinking)

    async def start(self) -> None:
        """
        Initialise the assistant (no-op for Completion).
        """
        pass

    async def complete(self, prompt: str) -> ChatCompletionMessage:
        """
        Generate a completion for the given prompt.

        :param prompt: The prompt to complete.
        :return: The completion message.
        """
        new_prompt = MessageDict(
            role="user",
            content=prompt,
        )
        await self.remember(new_prompt)
        temp_memory = self.clean_audio_messages()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=cast(list[dict[str, str]], temp_memory),
            reasoning_effort=self.reasoning["effort"] if self.reasoning else NotGiven,
        )
        message = response.choices[0].message
        await self.remember({"role": "assistant", "content": message.content or ""})
        return response.choices[0].message

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """
        Converse with the assistant using the chat completion API.

        :param user_input: The user's input message.
        :param thread_id: Optional thread ID (not used in Completion, required by interface).
        :return: MessageData containing the assistant's response and thread ID (if applicable).
        """
        if not user_input:
            return None

        message = await self.complete(user_input)
        return MessageData(
            text_content=message.content or "", thread_id=self.conversation_id
        )

    async def complete_audio(self, user_input: str) -> Union[bytes, str, None]:
        """
        Converse with the assistant using the chat completion API.

        :param user_input: The user's input message.
        :return: bytes containing the assistant's response in wav format.
        """
        if not user_input:
            return None
        import base64

        new_prompt = MessageDict(
            role="user",
            content=user_input,
        )
        await self.remember(new_prompt)
        temp_memory = deepcopy(self.memory)

        # Create a default message if needed
        default_message = {"role": "user", "content": user_input}

        # Process system message if it exists
        if temp_memory and temp_memory[0]["role"] == "system":
            message = temp_memory[0]
            if "You should always respond in audio format." not in message["content"]:
                message["content"] = f"""\
You should always respond in audio format.

{message["content"]}
"""

        complete = False
        while not complete:
            if not temp_memory or all(msg.get("audio") is None for msg in temp_memory):
                # Use the user input as the only message if memory is empty
                temp_memory = [default_message]
            try:
                completion = self.client.chat.completions.create(
                    model="gpt-4o-audio-preview",
                    modalities=["text", "audio"],
                    audio=ChatCompletionAudioParam(
                        voice="ballad",
                        format="wav",
                    ),
                    messages=temp_memory,
                )

            except BadRequestError as e:
                if e.body.get("code") == "audio_not_found":
                    idx = int(e.body["param"].split("[")[-1].split("]")[0])
                    del temp_memory[idx]["audio"]
                    continue
                raise
            complete = True

        response = completion.choices[0].message

        if response.audio and hasattr(response.audio, "data"):
            await self.remember(
                {
                    "role": "assistant",
                    "audio": {"id": response.audio.id},
                    "content": f"[AUDIO TRANSCRIPTION]: {response.content}",
                }
            )
            return base64.b64decode(response.audio.data)
        else:
            await self.remember(
                {"role": "assistant", "content": response.content or ""}
            )

        return response.content

    @property
    def conversation_payload(self) -> list[MessageDict]:
        return self.memory
