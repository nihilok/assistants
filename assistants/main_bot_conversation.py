import asyncio
import os

from assistants.telegram_ui.bot_conversation_bot import main

if __name__ == "__main__":
    # Check if required environment variables are set
    if not os.environ.get("MAIN_BOT_TOKEN") or not os.environ.get(
        "SECONDARY_BOT_TOKEN"
    ):
        print(
            "Please set MAIN_BOT_TOKEN and SECONDARY_BOT_TOKEN environment variables."
        )
        exit(1)

    asyncio.run(main())
