import os

from bot.exceptions import ConfigError
from bot.log import logger

ASSISTANTS_API_KEY_NAME = os.environ.get("ASSISTANTS_API_KEY_NAME", "OPENAI_API_KEY")

try:
    OPENAI_API_KEY = os.environ[ASSISTANTS_API_KEY_NAME]
except KeyError as e:
    error = f"Missing required {ASSISTANTS_API_KEY_NAME} environment variable"
    logger.error(error)
    raise ConfigError(error) from e

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")
CODE_MODEL = os.environ.get("CODE_MODEL", "o1-mini")
ASSISTANT_INSTRUCTIONS = os.environ.get(
    "ASSISTANT_INSTRUCTIONS", "You are a helpful assistant."
)
