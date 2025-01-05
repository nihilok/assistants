import asyncio

from assistants.cli import cli
from assistants.user_data.sqlite_backend import init_db


def main():
    asyncio.run(init_db())
    cli()


if __name__ == "__main__":
    main()
