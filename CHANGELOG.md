Changelog
---

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

- add `claude` command to automatically set relevant environment variables to use CLI with `claude-3-5-sonnet-latest` model.

---

### 29/01/2025 v0.5.1

- fix typo in setup.py preventing installation
- convert TerminalSelector to use label/value pairs instead of just strings of its values
- alters thread labels when selecting so that the thread id is not shown, just the initial prompt

---

### 12/01/2025 v0.5.0

- add support for image generation via OpenAI API
