import asyncio

from bot.ai.assistant import Assistant


def cli():
    assistant = Assistant(
        "default-assistant", "gpt-4o-mini", "You are a helpful assistant."
    )
    thread_id = None
    while (user_input := input(">>> ")).lower() not in {"q", "quit"}:
        if thread_id is None:
            run, message = asyncio.run(assistant.prompt(user_input))
            thread_id = run.thread_id
        else:
            run, message = asyncio.run(assistant.prompt(user_input, thread_id))
        print(
            assistant.client.beta.threads.messages.list(
                thread_id=run.thread_id, order="asc"
            )
            .data[-1]
            .content[0]
            .text.value
        )
