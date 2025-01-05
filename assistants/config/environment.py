import os

from assistants.lib.exceptions import ConfigError
from assistants.log import logger

ASSISTANTS_API_KEY_NAME = os.environ.get("ASSISTANTS_API_KEY_NAME", "OPENAI_API_KEY")

try:
    OPENAI_API_KEY = os.environ[ASSISTANTS_API_KEY_NAME]
    if not OPENAI_API_KEY:
        raise KeyError
except KeyError as e:
    error = f"Missing required {ASSISTANTS_API_KEY_NAME} environment variable"
    logger.error(error)
    raise ConfigError(error) from e

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")
CODE_MODEL = os.environ.get("CODE_MODEL", "o1-mini")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "dall-e-3")
ASSISTANT_INSTRUCTIONS = os.environ.get(
    "ASSISTANT_INSTRUCTIONS", "You are a helpful assistant."
)
HOME_DIR = os.environ["HOME"]
DB_TABLE = os.environ.get("USER_DATA_DB", f"{HOME_DIR}/.assistants_user_data.db")
