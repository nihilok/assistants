# Assistants Framework

Welcome to the AI Assistants Framework! This repository contains the foundational code for creating versatile AI assistants capable of interacting through various front-end interfaces and utilizing interchangeable data layers. The goal is to create a powerful yet flexible assistants framework that can adapt to different user needs and environments.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-Front-End Support**: The AI assistant (configured via environment variables) can interact through different user interfaces, including CLI and Telegram.
- **Interchangeable Data Layers**: Easily swap out the underlying data storage solutions, such as SQLite or other databases (coming soon).
- **Extensible Architecture**: Built with modularity in mind, allowing for easy addition of new features and integrations.
- **User Data Management**: Efficient handling of user data with a robust backend.

## Installation

To get started with the AI Assistant Project, follow these steps:

- Create a Python virtual environment (recommended, but not required on most systems) (Requires Python 3.10+)

(a simple way is to use the built-in `venv` module, e.g., `python -m venv my-venv; source my-venv/bin/activate`)

- Install the package using pip:

```bash
pip install assistants-framework
```

You can then run the following command to start the CLI:

```bash
$ ai-cli
```

NOTE: if your virtual environment is not activated, you may need to use /path/to/venv/bin/ai-cli instead of just ai-cli. Consider adding the virtual environment's bin directory to your PATH or otherwise linking the executable to a location in your PATH or creating an alias.

If you wish to use the Telegram bot interface, you can install the additional dependencies:

```bash
pip install assistants-framework[telegram]
```

## Usage

### Command Line Interface

For help running the assistant through the CLI, simply run:

```
$ ai-cli --help
usage: ai-cli [-h] [-e] [-f INPUT_FILE] [-i INSTRUCTIONS_FILE] [-t] [-C] [prompt ...]

CLI for AI Assistant

positional arguments:
  prompt                Positional arguments concatenate into a single prompt. E.g. `ai-cli
                        Is this a single prompt\?` (question mark escaped) ...will be passed
                        to the program as a single string (without the backslash). You can
                        also use quotes to pass a single argument with spaces and special
                        characters. See the -e and -f options for more advanced prompt
                        options.

options:
  -h, --help            show this help message and exit
  -e, --editor          Open the default editor to compose a prompt.
  -f INPUT_FILE, --input-file INPUT_FILE
                        Read the initial prompt from a file (e.g., 'input.txt').
  -i INSTRUCTIONS_FILE, --instructions INSTRUCTIONS_FILE
                        Read the initial instructions (system message) from a specified
                        file; if not provided, environment variable `ASSISTANT_INSTRUCTIONS`
                        or defaults will be used.
  -t, --continue-thread
                        Continue previous thread. (not currently possible with `-C` option)
  -C, --code            Use specialised reasoning/code model. WARNING: This model will be
                        slower and more expensive to use.
```


### Telegram Bot

To run the telegram bot polling loop, you can just use the following command:

```bash
$ ai-tg-bot
```

You can customize the behavior of the assistant by modifying the `ASSISTANT_INSTRUCTIONS` environment variable, which defaults to `"You are a helpful assistant."`

## Environment Variables

In addition to `ASSISTANT_INSTRUCTIONS`, other environment variables that can be configured include:

- `ASSISTANTS_API_KEY_NAME` - The name of the API key environment variable to use for authentication (defaults to `OPENAI_API_KEY`) - remember to also set the corresponding API key value to the environment variable you choose (or the default).
- `DEFAULT_MODEL` - The default model to use for OpenAI API requests (defaults to `gpt-4o-mini`)
- `CODE_MODEL` - more advanced reasoning model to use for OpenAI API requests (defaults to `o1-mini`)
- `TG_BOT_TOKEN` - The Telegram bot token if using the Telegram UI

## Contributing

Contributions are welcome! If you have suggestions for improvements, please feel free to submit a pull request or open an issue.

1. Fork the repository.
2. Commit your changes.
3. Open a pull request.

See the dev dependencies in the dev_requirements.txt file for formatting and linting tools.

#### TODOS: 

- optional local threads API built on top of langchain
- add postgresql support for data layer
- add support for more models/APIs

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Thank you for checking out the AI Assistant Project! I hope you find it useful and inspiring. Check out the examples directory to see the assistant in action!