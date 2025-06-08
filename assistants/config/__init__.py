import json
import os
from argparse import Namespace
from dataclasses import asdict, dataclass
from enum import Enum

from assistants.lib.constants import (
    DEFAULT_MAX_HISTORY_TOKENS,
    DEFAULT_MAX_RESPONSE_TOKENS,
)


class CustomKeyNames(str, Enum):
    ASSISTANTS_API_KEY_NAME: str = "ASSISTANTS_API_KEY_NAME"
    ANTHROPIC_API_KEY_NAME: str = "ANTHROPIC_API_KEY_NAME"
    MISTRAL_API_KEY_NAME: str = "MISTRAL_API_KEY_NAME"


@dataclass
class KeyNames:
    ASSISTANTS_API_KEY_NAME: str
    ANTHROPIC_API_KEY_NAME: str
    MISTRAL_API_KEY_NAME: str


def get_keynames():
    return KeyNames(
        ASSISTANTS_API_KEY_NAME=os.environ.get(
            CustomKeyNames.ASSISTANTS_API_KEY_NAME, "OPENAI_API_KEY"
        ),
        ANTHROPIC_API_KEY_NAME=os.environ.get(
            CustomKeyNames.ANTHROPIC_API_KEY_NAME, "ANTHROPIC_API_KEY"
        ),
        MISTRAL_API_KEY_NAME=os.environ.get(
            CustomKeyNames.MISTRAL_API_KEY_NAME, "MISTRAL_API_KEY"
        ),
    )


@dataclass
class Config:
    OPENAI_API_KEY: str  # pylint: disable=invalid-name
    ANTHROPIC_API_KEY: str  # pylint: disable=invalid-name
    MISTRAL_API_KEY: str  # pylint: disable=invalid-name
    DEFAULT_MODEL: str  # pylint: disable=invalid-name
    CODE_MODEL: str  # pylint: disable=invalid-name
    IMAGE_MODEL: str  # pylint: disable=invalid-name
    ASSISTANT_INSTRUCTIONS: str  # pylint: disable=invalid-name
    TELEGRAM_BOT_TOKEN: str  # pylint: disable=invalid-name
    DEFAULT_MAX_HISTORY_TOKENS: int  # pylint: disable=invalid-name
    DEFAULT_MAX_RESPONSE_TOKENS: int  # pylint: disable=invalid-name
    OPEN_IMAGES_IN_BROWSER: bool  # pylint: disable=invalid-name

    def update_from_config_yaml(self, config):
        """
        Update the environment variables from a YAML file.
        """
        env_dict = asdict(self)
        for key, value in config.items():
            if key in env_dict:
                setattr(self, key, value)


def update_args_from_config_file(config, args: Namespace):
    """
    Update the command line arguments from a YAML file.
    """
    for key, value in config.items():
        if key in args:
            setattr(args, key, value)


def get_config() -> Config:
    """
    Get the configuration from environment variables.
    """
    custom_keys = get_keynames()
    return Config(
        OPENAI_API_KEY=os.environ.get(custom_keys.ASSISTANTS_API_KEY_NAME, None),
        ANTHROPIC_API_KEY=os.environ.get(custom_keys.ANTHROPIC_API_KEY_NAME, None),
        MISTRAL_API_KEY=os.environ.get(custom_keys.MISTRAL_API_KEY_NAME, None),
        DEFAULT_MODEL=os.environ.get("DEFAULT_MODEL", "gpt-4o-mini"),
        CODE_MODEL=os.environ.get("CODE_MODEL", "o4-mini"),
        IMAGE_MODEL=os.environ.get("IMAGE_MODEL", "dall-e-3"),
        ASSISTANT_INSTRUCTIONS=os.environ.get(
            "ASSISTANT_INSTRUCTIONS", "You are a helpful assistant."
        ),
        TELEGRAM_BOT_TOKEN=os.environ.get("TG_BOT_TOKEN", None),
        DEFAULT_MAX_HISTORY_TOKENS=int(
            os.environ.get("DEFAULT_MAX_TOKENS", DEFAULT_MAX_HISTORY_TOKENS)
        ),
        DEFAULT_MAX_RESPONSE_TOKENS=int(
            os.environ.get("DEFAULT_MAX_RESPONSE_TOKENS", DEFAULT_MAX_RESPONSE_TOKENS)
        ),
        OPEN_IMAGES_IN_BROWSER=bool(
            json.loads(os.environ.get("OPEN_IMAGES_IN_BROWSER", "true"))
        ),
    )


environment = get_config()
