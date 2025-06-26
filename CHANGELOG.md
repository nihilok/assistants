Changelog
---

### 27/06/2025 v0.7.4

- fix issue calling non-existent `save_conversation_state` method in AssistantIoHandler

### 16/06/2025 v0.7.3

- fix typechecking errors and add mypy GH workflow
- update minimum Python version to 3.11
- add `ai-cli migrate` command to run migrations easily

### 08/06/2025 v0.7.2

- add command to print current environment variables (`/env`)

### 08/06/2025 v0.7.1

- add support for Mistral API
- refactor Assistant interfaces to support Mistral models and be more consistent across providers
- refactor database models for consistency, introducing Table interface for different tables.
- adds response streaming support for OpenAI and Claude models in the CLI (not yet available for Mistral)
- update tests to cover new functionality/interfaces

### 26/04/2025 v0.6.13

- fix mismatch between Completion reasoning_effort and Assistants API reasoning_effort

### 26/04/2025 v0.6.12

- refactor Assistant interfaces for better separation of concerns
- refactor io_loop.py functions into stateful methods on AssistantIoHandler class
- improve thinking/reasoning mode handling across providers for better consistency
- add `/thinking` command to toggle thinking mode in the CLI
- add `--opus` option to the CLI to use the Opus model for Claude 4 (alias of `--code`)

### 24/04/2025 v0.6.11

- add streaming response support for OpenAI models in the CLI
- improve streaming code highlighting in the CLI (now line-by-line)

### 24/04/2025 v0.6.10

- fix issue with version not available in installed package

### 24/05/2025 v0.6.9

- add support for claude 4 (sonnet/opus) models
- add streaming response support for Claude in the CLI

### 10/04/2025 v0.6.6

- update default code model to `o4-mini`

### 10/04/2025 v0.6.5

- improved README.md with more detailed description of the Telegram UI
- added mention of voice response capability in documentation
- various minor improvements and bug fixes

### 09/04/2025 v0.6.1

- add `tiktoken` as a dependency to setup.py

### 08/04/2025 v0.6

- switch out "Assistants API" for "Responses API" when using OpenAI models
- all interfaces now use the local Conversations API (Formerly MemoryMixin)
- MemoryMixin renamed to ConversationHistoryMixin
- remove threads table no longer required, drop table in rebuild db function.
- minor version upgrade requires rebuild of database

### 13/03/2025 v0.5.13

- fix dependency issue with pygments-tsx

---

### 13/03/2025 v0.5.12

- fix issue with thinking mode in Claude where ThinkingBlock objects were not being handled correctly
- fix issue with code highlighting where tsx was not supported by Pygments
- adds pygments-tsx as a dependency

---

### 12/03/2025 v0.5.11

- update README.md
- other refactors and improvements

---

### 12/03/2025 v0.5.10

- add CLI option to set variables and options from a config file (`-c`, `--config-file`)
- fixes bug where instructions were not being passed to the model via environment variable

---

### 10/03/2025 v0.5.9

- Update CODE_MODEL default to "o3-mini"
- add thinking mode options (command line option `-T`, `--thinking`)
- implement last message retrieval cli command (`/l`, `/last`)

---

### 07/03/2025 v0.5.8

- add support for `claude-3-7-sonnet-latest` model with "thinking" param if used as code model
- add support for `o1` and `o3-mini` used via the Assistants API (with reasoning_effort defaulting to "medium")
- fix logic causing conversations to be continued even without passing the continue thread flag

---

### 26/02/2025 v0.5.5

- add support for stdin redirection
- add support for new models
- add dummy-model for testing/debugging
- fix duplicated output when using the `/e` (editor) command

---

### 31/01/2025 v0.5.3

- add install command to add environment's bin directory to the PATH
- update README.md

---

### 30/01/2025 v0.5.2

- add `claude` command to automatically set relevant environment variables to use CLI with `claude-3-5-sonnet-latest`
  model.

---

### 29/01/2025 v0.5.1

- fix typo in setup.py preventing installation
- convert TerminalSelector to use label/value pairs instead of just strings of its values
- alters thread labels when selecting so that the thread id is not shown, just the initial prompt

---

### 12/01/2025 v0.5.0

- add support for image generation via OpenAI API
