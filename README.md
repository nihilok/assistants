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

- **Multi-Front-End Support**: The AI assistant can interact through different user interfaces, including CLI and Telegram.
- **Interchangeable Data Layers**: Easily swap out the underlying data storage solutions, such as SQLite or other databases.
- **Extensible Architecture**: Built with modularity in mind, allowing for easy addition of new features and integrations.
- **User Data Management**: Efficient handling of user data with a robust backend.

## Installation

To get started with the AI Assistant Project, follow these steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/nihilok/assistants.git
   cd assistants
   ```

2. **Install the dependencies**:

   For production dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   For development dependencies:

   ```bash
   pip install -r dev_requirements.txt
   ```

## Usage

### Command Line Interface

To interact with the assistant through the CLI, simply run:

```bash
python -m cli
```

### Telegram Bot

To set up the Telegram bot, ensure you have the necessary API tokens configured as specified in `environment.py`, then run:

```bash
python -m telegram_ui.tg_bot
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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Thank you for checking out the AI Assistant Project! I hope you find it useful and inspiring.
