#!/usr/bin/env python3
"""
Example script demonstrating the new UniversalAssistant usage.

This script shows how to migrate from the legacy provider-specific classes
to the new unified UniversalAssistant that uses the univllm library.
"""

import asyncio
import os
from assistants.ai import UniversalAssistant, create_universal_assistant


async def main():
    """Demonstrate UniversalAssistant usage with different providers."""

    print("=== UniversalAssistant Demo ===\n")

    # Example 1: Using OpenAI GPT-4
    print("1. Using OpenAI GPT-4:")
    try:
        openai_assistant = UniversalAssistant(
            model="gpt-4o",  # Model name auto-detects provider
            instructions="You are a helpful AI assistant.",
            max_response_tokens=150,
        )

        await openai_assistant.start()
        response = await openai_assistant.converse("What is machine learning?")
        if response:
            print(f"Response: {response.text_content[:100]}...")
        print()
    except Exception as e:
        print(f"Error with OpenAI: {e}\n")

    # Example 2: Using Anthropic Claude
    print("2. Using Anthropic Claude:")
    try:
        claude_assistant = UniversalAssistant(
            model="claude-4-sonnet",  # Auto-detects Anthropic
            instructions="You are Claude, an AI assistant.",
            max_response_tokens=150,
        )

        await claude_assistant.start()
        response = await claude_assistant.converse("Explain quantum computing briefly.")
        if response:
            print(f"Response: {response.text_content[:100]}...")
        print()
    except Exception as e:
        print(f"Error with Claude: {e}\n")

    # Example 3: Using convenience function
    print("3. Using convenience function:")
    try:
        assistant = create_universal_assistant(
            model="deepseek-chat",  # Auto-detects Deepseek
            instructions="You are a coding assistant.",
            max_response_tokens=100,
        )

        await assistant.start()
        response = await assistant.converse("What is Python?")
        if response:
            print(f"Response: {response.text_content[:100]}...")
        print()
    except Exception as e:
        print(f"Error with Deepseek: {e}\n")

    # Example 4: Streaming response
    print("4. Streaming response example:")
    try:
        streaming_assistant = UniversalAssistant(
            model="gpt-4o",
            instructions="You are a helpful assistant.",
        )

        await streaming_assistant.start()
        print("Stream: ", end="")
        async for chunk in streaming_assistant.stream_converse(
            "Tell me a very short joke."
        ):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"Error with streaming: {e}\n")


def migration_examples():
    """Show migration examples from legacy to new API."""

    print("=== Migration Examples ===\n")

    print("BEFORE (Legacy - Deprecated):")
    print(
        """
from assistants.ai.openai import OpenAIAssistant
from assistants.ai.anthropic import ClaudeAssistant

# Separate classes for each provider
openai_assistant = OpenAIAssistant(
    model="gpt-4o",
    instructions="You are helpful.",
    api_key="your-key"
)

claude_assistant = ClaudeAssistant(
    model="claude-4-sonnet",
    instructions="You are Claude.",
    api_key="your-key"
)
"""
    )

    print("AFTER (New - Recommended):")
    print(
        """
from assistants.ai import UniversalAssistant

# Single class for all providers
assistant = UniversalAssistant(
    model="gpt-4o",  # Provider auto-detected
    instructions="You are helpful.",
    api_key="your-key"  # Or use environment variables
)

# Same interface for different providers
claude_assistant = UniversalAssistant(
    model="claude-4-sonnet",  # Provider auto-detected
    instructions="You are Claude.",
)
"""
    )

    print("\nBenefits of the new approach:")
    print("✓ Single unified interface for all providers")
    print("✓ Automatic provider detection from model name")
    print("✓ Consistent API across all LLM providers")
    print("✓ Better error handling and provider abstraction")
    print("✓ Built on the mature univllm library")
    print("✓ Future-proof for new provider additions")


if __name__ == "__main__":
    # Show migration examples first
    migration_examples()

    # Then run the demo (requires API keys)
    if any(
        key in os.environ
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"]
    ):
        print("\n" + "=" * 50 + "\n")
        asyncio.run(main())
    else:
        print("\nTo run the demo, set environment variables:")
        print("export OPENAI_API_KEY='your-openai-key'")
        print("export ANTHROPIC_API_KEY='your-anthropic-key'")
        print("export DEEPSEEK_API_KEY='your-deepseek-key'")
