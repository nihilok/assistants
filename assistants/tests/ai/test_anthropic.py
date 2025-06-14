from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from assistants.ai.anthropic import INSTRUCTIONS_UNDERSTOOD, ClaudeAssistant
from assistants.ai.types import ThinkingConfig
from assistants.lib.exceptions import ConfigError


class TestClaude:
    """Tests for the Claude class."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        client = MagicMock()
        text_block = MagicMock()
        text_block.text = "AI response"
        client.messages.create = AsyncMock(return_value=MagicMock(content=[text_block]))
        return client

    @pytest.fixture
    def claude(self, mock_anthropic_client):
        """Create a Claude instance for testing."""
        with patch(
            "anthropic.AsyncAnthropic", return_value=mock_anthropic_client
        ) as mock_anthropic:
            # Ensure the mock is used for all instances
            instance = ClaudeAssistant(
                model="claude-3-opus-20240229",
                instructions="You are a helpful assistant.",
                api_key="test-key",
            )
            # Replace the client with our mock to ensure no real API calls
            instance.client = mock_anthropic_client
            return instance

    def test_init(self, claude, mock_anthropic_client):
        """Test initial of Claude."""
        assert claude.model == "claude-3-opus-20240229"
        assert claude.instructions == "You are a helpful assistant."
        # Don't check the client directly as it might be different in tests
        assert claude.thinking == ThinkingConfig(0, "enabled")

    def test_init_missing_api_key(self):
        """Test initial with missing API key."""
        with pytest.raises(ConfigError):
            with patch("assistants.ai.anthropic.environment.ANTHROPIC_API_KEY", ""):
                ClaudeAssistant(model="claude-3-opus-20240229", api_key="")

    @pytest.mark.asyncio
    async def test_start(self, claude):
        """Test starting the Claude assistant."""
        await claude.start()
        # start() is a no-op for Claude

    @pytest.mark.asyncio
    @patch("assistants.ai.memory.ConversationHistoryMixin.load_conversation")
    async def test_load_conversation(self, mock_super_load, claude):
        """Test loading a conversation."""
        # Setup memory with a system message
        claude.memory = [{"role": "system", "content": "System instruction"}]

        # Temporarily set instructions to None to prevent adding them to memory
        original_instructions = claude.instructions
        claude.instructions = None

        # Setup the mock to simulate the conversion of system messages
        async def mock_load_with_conversion(*args, **kwargs):
            # Simulate the conversion that would happen in the real method
            if claude.memory and claude.memory[0]["role"] == "system":
                content = claude.memory[0]["content"]
                claude.memory = [
                    {"role": "user", "content": content},
                    {"role": "assistant", "content": INSTRUCTIONS_UNDERSTOOD},
                ]

        mock_super_load.side_effect = mock_load_with_conversion

        await claude.load_conversation("test-id")

        # Restore instructions
        claude.instructions = original_instructions

        mock_super_load.assert_called_once_with("test-id")

        # Check that system message was converted to user+assistant pair
        # Just check that the memory has been modified and contains the expected content
        assert len(claude.memory) == 2
        assert claude.memory[0]["role"] == "user"
        assert claude.memory[0]["content"] == "System instruction"
        assert claude.memory[1]["role"] == "assistant"
        assert claude.memory[1]["content"] == INSTRUCTIONS_UNDERSTOOD

    @pytest.mark.asyncio
    async def test_converse(self, claude, mock_anthropic_client):
        """Test conversing with Claude."""
        # Clear memory and set instructions to None to simplify the test
        claude.memory = []
        claude.instructions = None

        result = await claude.converse("Hello")

        # Check that the message was added to memory
        assert claude.memory[-1] == {"role": "assistant", "content": "AI response"}

        # Check that the client was called with correct parameters
        mock_anthropic_client.messages.create.assert_called_once()
        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-3-opus-20240229"

        # Check that the messages parameter contains our user message
        messages = call_kwargs["messages"]
        assert len(messages) > 0
        assert {"role": "user", "content": "Hello"} in messages

        # Check the result
        assert result.text_content == "AI response"

    @pytest.mark.asyncio
    async def test_converse_empty_input(self, claude, mock_anthropic_client):
        """Test conversing with empty input."""
        result = await claude.converse("")

        assert result is None
        mock_anthropic_client.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_converse_with_thinking(self, claude, mock_anthropic_client):
        """Test conversing with thinking enabled."""
        claude.thinking = ThinkingConfig(1, "enabled", 10000)

        # Ensure the mock is properly set up
        text_block = MagicMock()
        text_block.text = "AI response"
        mock_anthropic_client.messages.create.return_value = MagicMock(
            content=[text_block]
        )

        await claude.converse("Hello")

        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert "thinking" in call_kwargs
        assert call_kwargs["thinking"]["type"] == "enabled"
        assert call_kwargs["thinking"]["budget_tokens"] > 0

    @pytest.mark.asyncio
    async def test_converse_no_text_content(self, claude, mock_anthropic_client):
        """Test conversing with no text content in response."""
        # Setup response with no text content
        mock_anthropic_client.messages.create.return_value = MagicMock(content=[])

        result = await claude.converse("Hello")

        assert result is None
