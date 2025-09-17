"""
AI module for the assistants package.

This module provides unified access to multiple LLM providers through the UniversalAssistant class,
which uses the univllm library. Legacy provider-specific classes are still available but deprecated.

Recommended imports:
    from assistants.ai import UniversalAssistant
    from assistants.ai.universal import create_universal_assistant

Legacy imports (deprecated):
    from assistants.ai.openai import OpenAIAssistant
    from assistants.ai.anthropic import ClaudeAssistant
    from assistants.ai.mistral import MistralAssistant
"""

# New unified interface (recommended)
from assistants.ai.universal import UniversalAssistant, create_universal_assistant

# Legacy imports (deprecated but still available)
from assistants.ai.openai import OpenAIAssistant, OpenAICompletion
from assistants.ai.anthropic import ClaudeAssistant
from assistants.ai.mistral import MistralAssistant

# Common types and utilities
from assistants.ai.types import (
    AssistantInterface,
    StreamingAssistantInterface,
    MessageData,
    MessageDict,
    ThinkingConfig,
)
from assistants.ai.memory import ConversationHistoryMixin

__all__ = [
    # New unified interface
    "UniversalAssistant",
    "create_universal_assistant",

    # Legacy classes (deprecated)
    "OpenAIAssistant",
    "OpenAICompletion",
    "ClaudeAssistant",
    "MistralAssistant",

    # Types and utilities
    "AssistantInterface",
    "StreamingAssistantInterface",
    "MessageData",
    "MessageDict",
    "ThinkingConfig",
    "ConversationHistoryMixin",
]
