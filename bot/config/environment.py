import os

from bot.exceptions import ConfigError
from bot.log import logger

try:
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
except KeyError as e:
    error = "Missing required OPENAI_API_KEY environment variable"
    logger.error(error)
    raise ConfigError(error) from e

ASSISTANT_INSTRUCTIONS = os.environ.get(
    "ASSISTANT_INSTRUCTIONS", "You are a helpful assistant."
)
