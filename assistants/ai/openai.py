"""
This module defines classes for interacting with the OpenAI API(s), including memory management functionality through the MemoryMixin class.

Classes:
    - Assistant: Encapsulates interactions with the OpenAI Assistants API.
    - Completion: Encapsulates interactions with the OpenAI Chat Completion API.
"""

import asyncio
import hashlib
from typing import Optional, Literal, Any, cast, TypeGuard

import openai

from openai._types import NOT_GIVEN, NotGiven
from openai.types.beta import Thread, Assistant as OpenAIAssistant
from openai.types.beta.threads import Message, Run
from openai.types.chat import ChatCompletionMessage

from assistants.ai.constants import REASONING_MODELS
from assistants.ai.memory import MemoryMixin
from assistants.ai.types import MessageData, MessageDict, AssistantInterface
from assistants.config import environment
from assistants.lib.exceptions import ConfigError, NoResponseError
from assistants.log import logger
from assistants.user_data import threads_table
from assistants.user_data.sqlite_backend.assistants import (
    get_assistant_data,
    save_assistant_id,
)
from assistants.user_data.sqlite_backend.threads import get_last_thread_for_assistant

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
        reasoning_effort (Optional[OpenAIThinkingLevel]): Reasoning effort for the model.
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
            self.reasoning_effort = THINKING_MAP[thinking]
            valid = True

        if not valid:
            raise ConfigError(
                f"Invalid thinking level: {thinking}. Must be 0, 1, or 2."
            )


class Assistant(
    ReasoningModelMixin, AssistantInterface
):  # pylint: disable=too-many-instance-attributes
    """
    Encapsulates interactions with the OpenAI Assistants API.

    Implements AssistantInterface: Interface for assistant classes.

    Attributes:
        name (str): The name of the assistant.
        model (str): The model to be used by the assistant.
        instructions (str): Instructions for the assistant.
        tools (list | NotGiven): Optional tools for the assistant.
        client (openai.OpenAI): Client for interacting with the OpenAI API.
        _config_hash (Optional[str]): Hash of the current configuration.
        assistant (Optional[openai.types.beta.Assistant]): The assistant object.
        last_message (Optional[Message]): The last message in the thread.
        last_prompt (Optional[str]): The last prompt sent to the assistant.
        reasoning_effort (Optional[OpenAIThinkingLevel]): Reasoning effort for the assistant.
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

        self.client = openai.OpenAI(
            api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        self.instructions = instructions
        self.model = model
        self.tools = tools
        self.name = name
        self._config_hash: Optional[str] = None
        self.assistant: Optional[OpenAIAssistant] = None
        self.last_message: Optional[Message] = None
        self.last_prompt: Optional[str] = None
        self.reasoning_effort: Optional[OpenAIThinkingLevel] = None
        self.reasoning_model_init(thinking)

    async def start(self) -> None:
        """
        Load the assistant_id from DB if exists or create a new assistant.
        """
        if not self.__dict__.get("assistant"):
            self.assistant = await self.load_or_create_assistant()
        self.last_message = None

    async def async_get_conversation_id(self) -> str:
        """
        Get the current conversation/thread ID.

        :return: The thread ID of the current conversation.
        """
        if self.last_message:
            return self.last_message.thread_id
        thread = await get_last_thread_for_assistant(self.assistant_id)
        return thread.thread_id

    def __getattribute__(self, item: str) -> Any:
        """
        Override to check if the assistant is loaded before accessing it.

        :param item: The attribute name.
        :return: The attribute value.
        """
        if item == "assistant":
            if self.__dict__.get("assistant") is None:
                raise AttributeError("Assistant not loaded. Call `start` method.")
        return super().__getattribute__(item)

    @property
    def assistant_id(self) -> str:
        """
        Get the assistant ID.

        :return: The assistant ID.
        """
        return self.assistant.id

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

    async def load_or_create_assistant(self) -> Any:
        """
        Get any existing assistant ID / config hash from the database or create a new assistant.

        :return: The assistant object.
        """
        existing_id, config_hash = await get_assistant_data(self.name, self.config_hash)
        if existing_id:
            try:
                assistant = self.client.beta.assistants.retrieve(existing_id)
                if config_hash != self.config_hash:
                    logger.info("Config has changed, updating assistant...")
                    self.client.beta.assistants.update(
                        existing_id,
                        instructions=self.instructions,
                        model=self.model,
                        tools=self.tools,
                        name=self.name,
                        reasoning_effort=self.reasoning_effort,
                    )
                    await save_assistant_id(self.name, assistant.id, self.config_hash)
                return assistant
            except openai.NotFoundError:
                pass
        assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            model=self.model,
            tools=self.tools,
            reasoning_effort=self.reasoning_effort,
        )
        await save_assistant_id(self.name, assistant.id, self.config_hash)
        return assistant

    def _create_thread(self, messages=NOT_GIVEN) -> Thread:
        """
        Create a new thread.

        :param messages: Optional initial messages for the thread.
        :return: The created thread.
        """
        return self.client.beta.threads.create(messages=messages)

    def _new_thread(self) -> Thread:
        """
        Create a new thread.

        :return: The created thread.
        """
        thread = self._create_thread()
        return thread

    def start_thread(self, prompt: str) -> Thread:
        """
        Create a new thread and add the first message to it.

        :param prompt: The initial prompt for the thread.
        :return: The created thread.
        """
        logger.debug(f"Starting new thread with prompt: {prompt}")
        thread = self._new_thread()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )
        return thread

    def continue_thread(self, prompt: str, thread_id: str) -> Message:
        """
        Add a new message to an existing thread.

        :param prompt: The message content.
        :param thread_id: The ID of the thread to continue.
        :return: The created message.
        """
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt,
        )
        return message

    def run_thread(self, thread: Thread) -> Run:
        """
        Run the thread using the current assistant.

        :param thread: The thread to run.
        :return: The run object.
        """
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
        )
        return run

    def _get_thread(self, thread_id: str) -> Thread:
        """
        Retrieve a thread by its ID.

        :param thread_id: The ID of the thread to retrieve.
        :return: The retrieved thread.
        """
        return self.client.beta.threads.retrieve(thread_id)

    async def prompt(self, prompt: str, thread_id: Optional[str] = None) -> Run:
        """
        Create a message using the prompt and add it to an existing thread or create a new thread.

        :param prompt: The message content.
        :param thread_id: Optional ID of the thread to continue.
        :return: The run object.
        """
        self.last_prompt = prompt
        if thread_id is None:
            thread = self.start_thread(prompt)
            run = self.run_thread(thread)
            thread_id = thread.id
        else:
            thread = self._get_thread(thread_id)
            self.continue_thread(prompt, thread_id)
            run = self.run_thread(thread)
        while run.status in {"queued", "in_progress"}:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )
            await asyncio.sleep(0.5)
        return run

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

    def get_last_message(self, thread_id: str) -> Optional[MessageData]:
        """
        Get the last message from the specified thread.

        :param thread_id: The ID of the thread to get the last message from.
        :return: MessageData containing the text content and thread ID, or None if no message exists.
        :raises NoResponseError: If no new message is found after the current last_message.
        """
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc",
            after=self.last_message.id if self.last_message else NOT_GIVEN,
        ).data

        if not messages:
            return None

        last_message_in_thread = messages[-1]

        if self.last_message and last_message_in_thread.id == self.last_message.id:
            raise NoResponseError

        self.last_message = last_message_in_thread

        return MessageData(
            text_content=last_message_in_thread.content[0].text.value,
            thread_id=thread_id,
        )

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[MessageData]:
        """
        Converse with the assistant by creating or continuing a thread.

        :param user_input: The user's input message.
        :param thread_id: Optional ID of the thread to continue.
        :return: MessageData containing the assistant's response and thread ID, or None if no input.
        """
        if not user_input:
            return None

        if thread_id is None:
            run = await self.prompt(user_input)
            thread_id = run.thread_id
        else:
            await self.prompt(user_input, thread_id)

        return self.get_last_message(thread_id)

    async def save_conversation_state(self) -> str:
        """
        Save the state of the conversation to the database.

        :return: The thread ID of the saved conversation.
        """
        if not self.last_message:
            raise ValueError("No conversation to save")

        await threads_table.save_thread(
            self.last_message.thread_id, self.assistant_id, self.last_prompt or ""
        )
        return self.last_message.thread_id

    async def get_whole_thread(self) -> list[MessageDict]:
        """
        Get the whole thread of messages.

        :return: List of messages in the thread, each containing role and content.
        """
        if not self.last_message:
            return []

        messages = self.client.beta.threads.messages.list(
            thread_id=self.last_message.thread_id,
            order="asc",
        ).data

        return [
            {
                "role": message.role,
                "content": message.content[0].text.value,
            }
            for message in messages
        ]


class Completion(ReasoningModelMixin, MemoryMixin, AssistantInterface):
    """
    Encapsulates interactions with the OpenAI Chat Completion API.

    Inherits from:
        - MemoryMixin: Mixin class to handle memory-related functionality.
        - AssistantInterface: Interface for assistant classes.

    Attributes:
        model (str): The model to be used for completions.
        client (openai.OpenAI): Client for interacting with the OpenAI API.
        reasoning_effort (Optional[OpenAIThinkingLevel]): Reasoning effort for the model.
    """

    REASONING_MODELS = REASONING_MODELS

    def __init__(
        self,
        model: str,
        max_memory: int = 50,
        api_key: str = environment.OPENAI_API_KEY,
        thinking: ThinkingLevel = 2,
    ):
        """
        Initialize the Completion instance.

        :param model: The model to be used for completions.
        :param max_memory: Maximum number of messages to retain in memory.
        :param api_key: API key for OpenAI.
        :param thinking: Level of reasoning effort (0=low, 1=medium, 2=high).
        """
        if not api_key:
            raise ConfigError("Missing 'OPENAI_API_KEY' environment variable")

        MemoryMixin.__init__(self, max_memory)
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.reasoning_effort: Optional[OpenAIThinkingLevel] = None
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
        response = self.client.chat.completions.create(
            model=self.model,
            messages=cast(list[dict[str, str]], self.memory),
            reasoning_effort=self.reasoning_effort,
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
