import asyncio
import os
import sys

from assistants.cli import cli
from assistants.config import environment
from assistants.user_data.sqlite_backend import init_db

CLAUDE_SONNET_MODEL = os.getenv(
    "DEFAULT_CLAUDE_SONNET_MODEL", "claude-sonnet-4-20250514"
)
CLAUDE_OPUS_MODEL = os.getenv("DEFAULT_CLAUDE_OPUS_MODEL", "claude-opus-4-20250514")


def main():
    if not environment.ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY not set in environment variables.", file=sys.stderr)
        sys.exit(1)
    environment.DEFAULT_MODEL = CLAUDE_SONNET_MODEL
    environment.CODE_MODEL = CLAUDE_OPUS_MODEL
    asyncio.run(init_db())
    cli()


if __name__ == "__main__":
    main()
