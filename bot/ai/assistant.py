import asyncio
from typing import Optional

import openai
from openai._types import NOT_GIVEN
from openai.types.beta import Thread
from openai.types.beta.threads import Run, Message

from ..config.environment import OPENAI_API_KEY
from ..user_data.sqlite_backend.assistants import get_assistant_id, save_assistant_id


class Assistant:
    def __init__(
        self,
        name: str,
        model: str,
        instructions: str,
        tools: Optional[list] = NOT_GIVEN,
        api_key: str = OPENAI_API_KEY,
    ):
        self.client = openai.OpenAI(
            api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        self.instructions = instructions
        self.tools = tools
        self.model = model
        self.name = name
        loop = asyncio.get_event_loop()
        self.assistant = loop.run_until_complete(self.load_or_create_assistant())

    async def load_or_create_assistant(self):
        existing_id = await get_assistant_id(self.name)
        if existing_id:
            try:
                return self.client.beta.assistants.retrieve(existing_id)
            except openai.NotFoundError:
                pass
        assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            model=self.model,
            tools=self.tools,
        )
        await save_assistant_id(self.name, assistant.id)
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

    async def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Optional[Message]:
        if not user_input:
            return

        if thread_id is None:
            run = await self.prompt(user_input)
            thread_id = run.thread_id
        else:
            await self.prompt(user_input, thread_id)

        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id, order="asc"
        ).data

        return messages[-1]
