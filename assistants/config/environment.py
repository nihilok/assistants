import os

ASSISTANTS_API_KEY_NAME = os.environ.get("ASSISTANTS_API_KEY_NAME", "OPENAI_API_KEY")
OPENAI_API_KEY = os.environ.get(ASSISTANTS_API_KEY_NAME, None)

ANTHROPIC_API_KEY_NAME = os.environ.get("ANTHROPIC_API_KEY_NAME", "ANTHROPIC_API_KEY")
ANTHROPIC_API_KEY = os.environ.get(ANTHROPIC_API_KEY_NAME, None)

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gpt-4o-mini")
CODE_MODEL = os.environ.get("CODE_MODEL", "o1-mini")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "dall-e-3")

ASSISTANT_INSTRUCTIONS = os.environ.get(
    "ASSISTANT_INSTRUCTIONS", "You are a helpful assistant."
)
