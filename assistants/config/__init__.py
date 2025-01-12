import json
import os
from dataclasses import dataclass
from enum import Enum

from assistants.cli.constants import CLAUDE_CLI_MAX_TOKENS


class CustomKeyNames(str, Enum):
    ASSISTANTS_API_KEY_NAME: str = "ASSISTANTS_API_KEY_NAME"
    ANTHROPIC_API_KEY_NAME: str = "ANTHROPIC_API_KEY_NAME"


@dataclass
class KeyNames:
    ASSISTANTS_API_KEY_NAME: str
    ANTHROPIC_API_KEY_NAME: str


def get_keynames():
    return KeyNames(
        ASSISTANTS_API_KEY_NAME=os.environ.get(
            CustomKeyNames.ASSISTANTS_API_KEY_NAME, "OPENAI_API_KEY"
        ),
        ANTHROPIC_API_KEY_NAME=os.environ.get(
            CustomKeyNames.ANTHROPIC_API_KEY_NAME, "ANTHROPIC_API_KEY"
        ),
    )


@dataclass
class Config:
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    DEFAULT_MODEL: str
    CODE_MODEL: str
    IMAGE_MODEL: str
    ASSISTANT_INSTRUCTIONS: str
    ASSISTANT_NAME: str
    TELEGRAM_BOT_TOKEN: str
    CLAUDE_MAX_TOKENS: str
    OPEN_IMAGES_IN_BROWSER: bool


def get_config() -> Config:
    custom_keys = get_keynames()
    return Config(
        OPENAI_API_KEY=os.environ.get(custom_keys.ASSISTANTS_API_KEY_NAME, None),
        ANTHROPIC_API_KEY=os.environ.get(custom_keys.ANTHROPIC_API_KEY_NAME, None),
        DEFAULT_MODEL=os.environ.get("DEFAULT_MODEL", "gpt-4o-mini"),
        CODE_MODEL=os.environ.get("CODE_MODEL", "o1-mini"),
        IMAGE_MODEL=os.environ.get("IMAGE_MODEL", "dall-e-3"),
        ASSISTANT_INSTRUCTIONS=os.environ.get(
            "ASSISTANT_INSTRUCTIONS", "You are a helpful assistant."
        ),
        ASSISTANT_NAME=os.environ.get("ASSISTANT_NAME", "DefaultAssistant"),
        TELEGRAM_BOT_TOKEN=os.environ.get("TG_BOT_TOKEN", None),
        CLAUDE_MAX_TOKENS=os.environ.get("CLAUDE_MAX_TOKENS", CLAUDE_CLI_MAX_TOKENS),
        OPEN_IMAGES_IN_BROWSER=bool(
            json.loads(os.environ.get("OPEN_IMAGES_IN_BROWSER", "true"))
        ),
    )


environment = get_config()
