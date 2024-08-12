import asyncio

from bot.ai.assistant import Assistant
from bot.exceptions import NoResponseError


def cli():
    assistant = Assistant(
        "default-assistant", "gpt-4o-mini", "You are a helpful assistant."
    )
    thread_id = None
    last_message_id = None
    while (user_input := input(">>> ")).lower() not in {"q", "quit"}:
        if thread_id is None:
            run, message = asyncio.run(assistant.prompt(user_input))
            thread_id = run.thread_id
        else:
            run, message = asyncio.run(assistant.prompt(user_input, thread_id))

        messages = assistant.client.beta.threads.messages.list(
            thread_id=run.thread_id, order="asc"
        ).data

        if messages[-1].id == last_message_id:
            raise NoResponseError

        last_message_id = messages[-1].id
        print(messages[-1].content[0].text.value)
