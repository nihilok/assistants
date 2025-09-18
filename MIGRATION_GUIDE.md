# Migration Guide: Using UniversalAssistant with univllm

## Overview

The `assistants` package now uses the `univllm` library to provide a unified interface for multiple LLM providers. This replaces the previous provider-specific implementations while maintaining backward compatibility.

## What's New

- **Single Interface**: `UniversalAssistant` works with OpenAI, Anthropic, Deepseek, and Mistral
- **Auto-Detection**: Provider automatically detected from model name
- **Simplified API**: No need to import different classes for different providers
- **Better Error Handling**: Unified error handling across all providers
- **Future-Proof**: Easy to add new providers through univllm updates

## Quick Migration

### Before (Deprecated)
```python
from assistants.ai.openai import OpenAIAssistant
from assistants.ai.anthropic import ClaudeAssistant
from assistants.ai.mistral import MistralAssistant

# Different classes for each provider
openai_assistant = OpenAIAssistant(
    model="gpt-4o",
    instructions="You are helpful.",
    api_key="your-openai-key"
)

claude_assistant = ClaudeAssistant(
    model="claude-4-sonnet", 
    instructions="You are Claude.",
    api_key="your-anthropic-key"
)

mistral_assistant = MistralAssistant(
    model="mistral-large",
    instructions="You are helpful.",
    api_key="your-mistral-key"
)
```

### After (Recommended)
```python
from assistants.ai import UniversalAssistant

# Single class for all providers - provider auto-detected from model name
openai_assistant = UniversalAssistant(
    model="gpt-4o",  # Auto-detects OpenAI
    instructions="You are helpful."
    # Uses OPENAI_API_KEY from environment
)

claude_assistant = UniversalAssistant(
    model="claude-4-sonnet",  # Auto-detects Anthropic
    instructions="You are Claude."
    # Uses ANTHROPIC_API_KEY from environment
)

mistral_assistant = UniversalAssistant(
    model="mistral-large",  # Auto-detects Mistral
    instructions="You are helpful."
    # Uses MISTRAL_API_KEY from environment
)
```

## API Compatibility

The `UniversalAssistant` implements the same interface as the legacy classes:

```python
# All these methods work the same way
response = await assistant.converse("Hello")
async for chunk in assistant.stream_converse("Hello"):
    print(chunk, end="")
```

## Environment Variables

Set your API keys as environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key" 
export DEEPSEEK_API_KEY="your-deepseek-key"
export MISTRAL_API_KEY="your-mistral-key"
```

## Supported Models

The library automatically detects providers based on model prefixes:

| Provider | Model Prefixes | Example |
|----------|----------------|---------|
| OpenAI | `gpt-4o`, `gpt-5`, `o1-` | `gpt-4o`, `o1-preview` |
| Anthropic | `claude-3-`, `claude-4-` | `claude-4-sonnet` |
| Deepseek | `deepseek-chat`, `deepseek-coder` | `deepseek-chat` |
| Mistral | `mistral-`, `codestral-` | `mistral-large` |

## Convenience Functions

For even simpler usage:

```python
from assistants.ai.universal import create_universal_assistant

# Simple helper function
assistant = create_universal_assistant(
    model="gpt-4o",
    instructions="You are helpful."
)
```

## Legacy Code Support

Legacy imports still work but show deprecation warnings:

```python
# Still works but deprecated
from assistants.ai.openai import OpenAIAssistant  # Shows warning
from assistants.ai.anthropic import ClaudeAssistant  # Shows warning
```

## Error Handling

The new implementation provides better error messages:

```python
try:
    assistant = UniversalAssistant(model="unsupported-model")
except ConfigError as e:
    print(f"Configuration error: {e}")
```

## Benefits

1. **Unified Interface**: One class for all providers
2. **Auto-Detection**: No need to specify provider manually
3. **Consistent Behavior**: Same API across all providers
4. **Better Maintenance**: Built on the stable univllm library
5. **Future-Proof**: New providers added through univllm updates
6. **Simplified Dependencies**: Fewer direct provider dependencies

## Backward Compatibility

- All existing code continues to work
- Legacy classes remain available but deprecated
- Same method signatures and behavior
- Gradual migration path available

## Next Steps

1. Update imports to use `UniversalAssistant`
2. Remove provider-specific logic
3. Test with your existing workflows
4. Update documentation and examples
5. Consider removing legacy imports after testing
