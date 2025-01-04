import asyncio
import hashlib
from typing import Optional, TypedDict

import openai
from openai._types import NOT_GIVEN, NotGiven
from openai.types.beta import Thread
from openai.types.beta.threads import Message, Run
from openai.types.chat import ChatCompletionMessage

import config
from lib.exceptions import NoResponseError
from log import logger
from user_data.sqlite_backend.assistants import get_assistant_data, save_assistant_id


class Assistant:
    def __init__(
        self,
        name: str,
        model: str,
        instructions: str,
        tools: list | NotGiven = NOT_GIVEN,
        api_key: str = config.OPENAI_API_KEY,
    ):
        self.client = openai.OpenAI(
            api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        self.instructions = instructions
        self.tools = tools
        self.model = model
        self.name = name
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        self._config_hash = None
        self.assistant = loop.run_until_complete(self.load_or_create_assistant())
        self.last_message_id = None

    @property
    def config_hash(self):
        if not self._config_hash:
            self._config_hash = self.generate_config_hash()
        return self._config_hash

    def generate_config_hash(self):
        return hashlib.sha256(
            f"{self.instructions}{self.model}{self.tools}".encode()
        ).hexdigest()

    async def load_or_create_assistant(self):
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
        )
        await save_assistant_id(self.name, assistant.id, self.config_hash)
        return assistant

    def _create_thread(self, messages=NOT_GIVEN) -> Thread:
        return self.client.beta.threads.create(messages=messages)

    def new_thread(self) -> Thread:
        thread = self._create_thread()
        return thread

    def start_thread(self, prompt: str) -> Thread:
        thread = self.new_thread()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )
        return thread

    def continue_thread(self, prompt: str, thread_id: str) -> Message:
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt,
        )
        return message

    def run_thread(self, thread: Thread) -> Run:
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
        )
        return run

    def _get_thread(self, thread_id: str) -> Thread:
        return self.client.beta.threads.retrieve(thread_id)

    async def prompt(self, prompt: str, thread_id: Optional[str] = None) -> Run:
        if thread_id is None:
            thread = self.start_thread(prompt)
            run = self.run_thread(thread)
            thread_id = thread.id
        else:
            thread = self._get_thread(thread_id)
            self.continue_thread(prompt, thread_id)
            run = self.run_thread(thread)
        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )
            await asyncio.sleep(0.5)
        return run

    async def image_prompt(self, prompt: str) -> Optional[str]:
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[Message]:
        if not user_input:
            return None

        if thread_id is None:
            run = await self.prompt(user_input)
            thread_id = run.thread_id
        else:
            await self.prompt(user_input, thread_id)

        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id, order="asc", after=self.last_message_id or NOT_GIVEN
        ).data

        last_message_in_thread = messages[-1]

        if last_message_in_thread.id == self.last_message_id:
            raise NoResponseError

        self.last_message_id = last_message_in_thread.id

        return last_message_in_thread


class MessageDict(TypedDict):
    role: str
    content: str | None


class Completion:
    def __init__(
        self,
        model: str,
        max_memory: int = 50,
        api_key: str = config.OPENAI_API_KEY,
    ):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.memory: list[MessageDict] = []
        self.max_memory = max_memory

    def truncate_memory(self):
        self.memory = self.memory[-self.max_memory :]

    def complete(self, prompt: str) -> ChatCompletionMessage:
        new_prompt = MessageDict(
            role="user",
            content=prompt,
        )
        self.truncate_memory()
        self.memory.append(new_prompt)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.memory,  # type: ignore
        )
        message = response.choices[0].message
        self.memory.append({"role": "assistant", "content": message.content})
        return response.choices[0].message

    async def converse(self, user_input: str, *args, **kwargs) -> ChatCompletionMessage:
        return self.complete(user_input)
