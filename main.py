import asyncio

from cli import cli
from user_data.sqlite_backend import init_db


def main():
    asyncio.run(init_db())
    cli()

if __name__ == "__main__":
    main()
