import pytest
from unittest.mock import patch

from assistants.ai.dummy_assistant import DummyAssistant
from assistants.ai.types import MessageData


class TestDummyAssistant:
    """Tests for the DummyAssistant class."""

    @pytest.fixture
    def dummy_assistant(self):
        """Create a DummyAssistant instance for testing."""
        return DummyAssistant()

    def test_init(self, dummy_assistant):
        """Test initialisation of DummyAssistant."""
        assert dummy_assistant.max_history_tokens == 1
        assert dummy_assistant.memory == []
        assert dummy_assistant.conversation_id is None

    @pytest.mark.asyncio
    @patch("assistants.ai.memory.ConversationHistoryMixin.load_conversation")
    async def test_start(self, mock_load_conversation, dummy_assistant):
        """Test starting the DummyAssistant."""
        await dummy_assistant.start()
        mock_load_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_converse(self, dummy_assistant):
        """Test conversing with the DummyAssistant."""
        result = await dummy_assistant.converse("Hello")

        assert isinstance(result, MessageData)
        assert result.text_content == "Response to ```\nHello\n```"
        assert result.thread_id is None

    @pytest.mark.asyncio
    async def test_converse_empty_input(self, dummy_assistant):
        """Test conversing with empty input."""
        result = await dummy_assistant.converse("")

        assert result is None

    @pytest.mark.asyncio
    async def test_converse_ignores_args_kwargs(self, dummy_assistant):
        """Test that converse ignores additional args and kwargs."""
        # The method is static and should ignore thread_id and other arguments
        result = await dummy_assistant.converse("Hello", "thread-id", extra_arg="value")

        assert result.text_content == "Response to ```\nHello\n```"
