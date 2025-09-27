# Assistants Framework

A flexible framework for creating AI assistants with multiple frontend interfaces.

## Features

- **Multi-Front-End Support**: CLI and Telegram interfaces built on the same core framework
- **CLI Features**: Code highlighting, thread management, editor integration, file input, image generation
- **Multiple LLM Support**: OpenAI (`gpt-*`, `o*`), Anthropic (`claude-*`), MistralAI (`mistral-*`, `codestral-*`), and image generation (DALL-E)
- **New Universal Assistant Interface**: See MIGRATION_GUIDE.md for details

## Installation

Requires Python 3.11+

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
- `/thinking <level>` - Toggle thinking mode (for reasoning models)
- `/last` - Retrieve last message

Use the `claude` command for Anthropic models (Now defaults to Claude 4):

```bash
claude -e  # Open editor for Claude
```

There's also a `chatgpt` command that uses the default ChatGPT model:

```bash
chatgpt -t  # Continue the last thread with ChatGPT (`gpt-4.1-mini`)
```

Run migrations in case of breaking changes:

```bash
ai-cli migrate
```

Rebuild the database:

```bash
ai-cli rebuild
```

### Telegram Interface

The framework includes a Telegram bot interface with the following features:

- **User Management**: Authorise/deauthorise users and chats, promote/demote users
- **Thread Management**: Start new conversation threads
- **Auto-Reply Toggle**: Enable/disable automatic responses
- **Media Generation**: Generate images from text prompts
- **Voice Responses**: Generate audio responses with the `/voice` command

Key Telegram commands:

- `/new_thread` - Clear conversation history and start a new thread
- `/auto_reply` - Toggle automatic responses on/off
- `/image <prompt>` - Generate an image from a text prompt
- `/voice <text>` - Generate an audio response.

## Environment Variables

- `ASSISTANT_INSTRUCTIONS` - System message (default: "You are a helpful assistant")
- `ASSISTANTS_API_KEY_NAME` - API key variable name (default: `OPENAI_API_KEY`)
- `ANTHROPIC_API_KEY_NAME` - Anthropic API key variable (default: `ANTHROPIC_API_KEY`)
- `MISTRAL_API_KEY_NAME` - Mistral API key variable (default: `MISTRAL_API_KEY`)
- `DEFAULT_MODEL` - Default model (default: `gpt-5-mini`)
- `DEFAULT_CLAUDE_SONNET_MODEL` - Default Claude model (default: `claude-sonnet-4-20250514`)
- `DEFAULT_CLAUDE_OPUS_MODEL` - Default Claude Opus model (default: `claude-opus-4-1-20250805`)
- `DEFAULT_CHATGPT_MODEL` - Default ChatGPT model (default: `gpt-5-mini`)
- `DEFAULT_GPT_REASONING_MODEL` - Default GPT reasoning model (default: `o4-mini`)
- `CODE_MODEL` - Reasoning model (default: `o4-mini`)
- `IMAGE_MODEL` - Image model (default: `gpt-image-1`)
- `ASSISTANTS_DATA_DIR` - Data directory (default: `~/.local/share/assistants`)
- `ASSISTANTS_CONFIG_DIR` - Config directory (default: `~/.config/assistants`)
- `TG_BOT_TOKEN` - Telegram bot token
- `OPEN_IMAGES_IN_BROWSER` - Open images automatically (default: `true`)
- `DEFAULT_MAX_RESPONSE_TOKENS` - Default max response tokens (default: `4096`)
- `DEFAULT_MAX_HISTORY_TOKENS` - Default max history tokens (default: `10000`)

## File Tagging in Prompts

You can include the contents of files directly in your prompt by tagging them with an `@` followed by the file path. Both absolute and relative paths are supported. For example:

```
Hi Claude, can you check my @~/.zshrc and tell me what you think?
Hi Claude, can you check my @./my_local_config.txt and tell me what you think?
```

When you use a tag like `@/path/to/file.txt` or `@relative/path/to/file.txt` in your prompt, the assistant will automatically append the contents of that file to the end of your input, like this:

```
Hi Claude, can you check my @./my_local_config.txt and tell me what you think?

===./my_local_config.txt===
// file content
===EOF===
```

- You can tag multiple files in a single prompt; each will be appended in the same format.
- If a file cannot be read, an error message will be shown in place of its content.
- Both absolute (starting with `/`) and relative paths (like `./file.txt` or `subdir/file.txt`) are supported for tagging.

## Contributing

Contributions welcome! Fork the repository, make changes, and submit a pull request.

#### TODOs:

- Improved conversation handling/truncation for token limits - currently uses tiktoken for all models
- Additional model/API support
- Additional database support

## License

MIT License
