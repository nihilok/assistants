import asyncio
import sys

from assistants.cli import cli
from assistants.config import environment
from assistants.user_data.sqlite_backend import init_db

CLAUDE_MODEL = "claude-3-5-sonnet-latest"


def main():
    if not environment.ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY not set in environment variables.", file=sys.stderr)
        sys.exit(1)
    environment.DEFAULT_MODEL = CLAUDE_MODEL
    environment.CODE_MODEL = CLAUDE_MODEL
    environment.ASSISTANT_INSTRUCTIONS = ""
    asyncio.run(init_db())
    cli()


if __name__ == "__main__":
    main()
