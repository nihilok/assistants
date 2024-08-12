import asyncio
from typing import Optional

import openai
from openai._types import NotGiven
from openai.types.beta import Thread
from openai.types.beta.thread_create_and_run_params import ThreadMessage
from openai.types.beta.threads import Run, Message

from ..config.environment import OPENAI_API_KEY


class Assistant:
    def __init__(self, name: str, model: str, instructions: str):
        self.client = openai.OpenAI(
            api_key=OPENAI_API_KEY, default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        self.assistant = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
        )

    def _create_thread(self, messages=NotGiven()) -> Thread:
        return self.client.beta.threads.create(messages=messages)

    def new_thread(self) -> Thread:
        thread = self._create_thread()
        return thread

    def start_thread(self, prompt: str) -> tuple[Thread, ThreadMessage]:
        thread = self.new_thread()
        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
        )
        return thread, message

    def continue_thread(self, prompt: str, thread_id: str) -> ThreadMessage:
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
            thread, message = self.start_thread(prompt)
            run = self.run_thread(thread)
            thread_id = thread.id
        else:
            thread = self._get_thread(thread_id)
            message = self.continue_thread(prompt, thread_id)
            run = self.run_thread(thread)
        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )
            await asyncio.sleep(0.5)
        return run, message

    def converse(
        self, user_input: str, thread_id: Optional[str] = None
    ) -> Message | None:
        if not user_input:
            return

        if thread_id is None:
            run = asyncio.run(self.prompt(user_input))
            thread_id = run.thread_id
        else:
            asyncio.run(self.prompt(user_input, thread_id))

        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id, order="asc"
        ).data

        return messages[-1]
