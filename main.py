import asyncio

from cli import cli
from user_data.sqlite_backend import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
    cli()
