# Assistants Framework

A flexible framework for creating AI assistants with multiple frontend interfaces.

## Features

- **Multi-Front-End Support**: CLI and Telegram interfaces built on the same core framework
- **CLI Features**: Code highlighting, thread management, editor integration, file input, image generation
- **Multiple LLM Support**: OpenAI (`gpt-*`, `o*`), Anthropic (`claude-*`), and image generation (DALL-E)

## Installation

Requires Python 3.10+

```bash
pip install assistants-framework
```

For Telegram bot functionality:

```bash
pip install assistants-framework[telegram]
```

Add commands to your PATH:

```bash
ai-cli install
```



## Usage

### Command Line Interface

```bash
ai-cli --help
```

Key CLI commands (prefixed with `/`):
- `/help` - Show help message
- `/editor` - Open editor for prompt composition
- `/image <prompt>` - Generate an image
- `/copy` - Copy response to clipboard
- `/new` - Start new thread
- `/threads` - List and select threads
- `/last` - Retrieve last message

Use the `claude` command for Anthropic models:

```bash
claude -e  # Open editor for Claude
```


Rebuild the database:

```bash
ai-cli rebuild
```

## Environment Variables

- `ASSISTANT_INSTRUCTIONS` - System message (default: "You are a helpful assistant")
- `ASSISTANTS_API_KEY_NAME` - API key variable name (default: `OPENAI_API_KEY`)
- `ANTHROPIC_API_KEY_NAME` - Anthropic API key variable (default: `ANTHROPIC_API_KEY`)
- `DEFAULT_MODEL` - Default model (default: `gpt-4o-mini`)
- `CODE_MODEL` - Reasoning model (default: `o3-mini`)
- `IMAGE_MODEL` - Image model (default: `dall-e-3`)
- `ASSISTANTS_DATA_DIR` - Data directory (default: `~/.local/share/assistants`)
- `ASSISTANTS_CONFIG_DIR` - Config directory (default: `~/.config/assistants`)
- `TG_BOT_TOKEN` - Telegram bot token
- `OPEN_IMAGES_IN_BROWSER` - Open images automatically (default: `true`)
- `DEFAULT_MAX_RESPONSE_TOKENS` - Default max response tokens (default: `4096`)
- `DEFAULT_MAX_HISTORY_TOKENS` - Default max history tokens (default: `4096`)

## Contributing

Contributions welcome! Fork the repository, make changes, and submit a pull request.

#### TODOs:
- Improved conversation handling/truncation for token limits
- Additional model/API support
- Additional database support

## License

MIT License