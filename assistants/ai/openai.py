"""
This module defines classes for interacting with the OpenAI API(s), including memory management functionality through the MemoryMixin class.

Classes:
    - Assistant: Encapsulates interactions with the OpenAI Responses API.
    - Completion: Encapsulates interactions with the OpenAI Chat Completion API.
"""

import hashlib
from copy import deepcopy
from typing import Optional, Literal, Any, cast, TypeGuard, Dict, Union

import openai
from openai import BadRequestError
from openai._types import NOT_GIVEN, NotGiven
from openai.types.chat import ChatCompletionMessage, ChatCompletionAudioParam

from assistants.ai.constants import REASONING_MODELS
from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.types import MessageData, MessageDict, AssistantInterface
from assistants.config import environment
from assistants.lib.exceptions import ConfigError, NoResponseError

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
    Mixin class to handle reasoning model initialization.

    Attributes:
        reasoning (Optional[Dict]): Reasoning configuration for the model.
    """

    def reasoning_model_init(self, thinking: ThinkingLevel) -> None:
        """
        Initialize the reasoning model.
        """
        if self.model not in REASONING_MODELS:
            return

        self._set_reasoning_effort(thinking)

        if getattr(self, "tools", None):
            self.tools = NOT_GIVEN

    def _set_reasoning_effort(self, thinking: ThinkingLevel) -> None:
        valid = False
        try:
            thinking = int(thinking)
        except (ValueError, TypeError):
            valid = False

        if is_valid_thinking_level(thinking):
            if isinstance(self, Completion):
                self.reasoning = THINKING_MAP[thinking]
            else:
                self.reasoning = {"effort": THINKING_MAP[thinking]}
            valid = True

        if not valid:
            raise ConfigError(
                f"Invalid thinking level: {thinking}. Must be 0, 1, or 2."
            )


class Assistant(
    ReasoningModelMixin, ConversationHistoryMixin, AssistantInterface
):  # pylint: disable=too-many-instance-attributes
    """
    Encapsulates interactions with the OpenAI Responses API.

    Implements AssistantInterface: Interface for assistant classes.

    Attributes:
        name (str): The name of the assistant.
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

    REASONING_MODELS = REASONING_MODELS

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        name: str,
        model: str,
        instructions: str,
        tools: list | NotGiven = NOT_GIVEN,
        api_key: str = environment.OPENAI_API_KEY,
        thinking: ThinkingLevel = 1,
    ):
        """
        Initialize the Assistant instance.

        :param name: The name of the assistant.
        :param model: The model to be used by the assistant.
        :param instructions: Instructions for the assistant.
        :param tools: Optional tools for the assistant.
        :param api_key: API key for OpenAI.
        :param thinking: Level of reasoning effort (0=low, 1=medium, 2=high).
        """
        if not api_key:
            raise ConfigError("Missing 'OPENAI_API_KEY' environment variable")

        self.client = openai.OpenAI(api_key=api_key)
        self.instructions = instructions
        self.model = model
        self.tools = tools
        self.name = name
        self._config_hash: Optional[str] = None
        self.last_message: Optional[dict] = None
        self.last_prompt: Optional[str] = None
        self.reasoning: Optional[Dict[str, OpenAIThinkingLevel]] = None
        ConversationHistoryMixin.__init__(self)
        self.reasoning_model_init(thinking)

    async def start(self) -> None:
        """
        Initialize the message history with system instructions.
        """
        if self.instructions and not self.memory:
            self.remember({"role": "system", "content": self.instructions})
        self.last_message = None

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
            f"{self.name}{self.instructions}{self.model}{self.tools}".encode()
        ).hexdigest()

    async def prompt(self, prompt: str) -> Any:
        """
        Send a prompt to the model using the Responses API.

        :param prompt: The message content.
        :param thread_id: Optional ID of the conversation to continue.
        :return: The response object.
        """
        self.last_prompt = prompt

        input_messages = []

        # Add system message if instructions are available
        if self.instructions and not any(
            msg.get("role") == "system" for msg in self.memory
        ):
            input_messages.append({"role": "system", "content": self.instructions})

        # If we have history, use it
        temp_memory = self.clean_audio_messages()
        if temp_memory:
            input_messages.extend(temp_memory)

        # Add the new user message
        input_messages.append({"role": "user", "content": prompt})

        response = self.client.responses.create(
            model=self.model,
            input=input_messages if len(input_messages) > 1 else prompt,
            reasoning=self.reasoning,
            store=True,
        )

        # Update message history
        self.remember({"role": "user", "content": prompt})
        self.remember({"role": "assistant", "content": response.output_text})

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


class Completion(ReasoningModelMixin, ConversationHistoryMixin, AssistantInterface):
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
        thinking: ThinkingLevel = 2,
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
        self.reasoning: Optional[OpenAIThinkingLevel] = None
        self.reasoning_model_init(thinking)

    async def start(self) -> None:
        """
        Initialize the assistant (no-op for Completion).
        """
        pass

    def complete(self, prompt: str) -> ChatCompletionMessage:
        """
        Generate a completion for the given prompt.

        :param prompt: The prompt to complete.
        :return: The completion message.
        """
        new_prompt = MessageDict(
            role="user",
            content=prompt,
        )
        self.remember(new_prompt)
        temp_memory = self.clean_audio_messages()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=cast(list[dict[str, str]], temp_memory),
            reasoning_effort=self.reasoning,
        )
        message = response.choices[0].message
        self.remember({"role": "assistant", "content": message.content or ""})
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

        message = self.complete(user_input)
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
        self.remember({"role": "user", "content": user_input})
        temp_memory = deepcopy(self.memory)
        if (message := temp_memory[0])["role"] == "system":
            if "You should always respond in audio format." not in message["content"]:
                message[
                    "content"
                ] = f"""\
You should always respond in audio format.

{message["content"]}
"""
        complete = False
        while not complete:
            if all(message.get("audio") is None for message in temp_memory):
                temp_memory = [message]
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

        if response.audio:
            self.remember(
                {
                    "role": "assistant",
                    "audio": {"id": response.audio.id},
                    "content": f"[AUDIO TRANSCRIPTION]: {response.content}",
                }
            )
            return base64.b64decode(completion.choices[0].message.audio.data)
        else:
            self.remember({"role": "assistant", "content": response.content})

        return response.content


class RealtimeVoiceChat(ConversationHistoryMixin, AssistantInterface):
    async def start(self) -> None:
        pass

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        filename = user_input
        with open(filename, "rb") as f:
            audio = f.read()
