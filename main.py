import asyncio

from bot.cli import cli
from bot.user_data.sqlite_backend import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
    cli()
