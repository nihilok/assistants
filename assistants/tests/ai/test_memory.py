import pytest
from unittest.mock import patch
from datetime import datetime

from assistants.ai.memory import ConversationHistoryMixin
from assistants.ai.types import MessageData, MessageDict
from assistants.user_data.sqlite_backend.conversations import Conversation


class TestConversationHistoryMixin:
    """Tests for the ConversationHistoryMixin class."""

    @pytest.fixture
    def memory_mixin(self):
        """Create a concrete implementation of ConversationHistoryMixin for testing."""

        class ConcreteMemoryMixin(ConversationHistoryMixin):
            async def converse(self, user_input, thread_id=None):
                return MessageData(
                    text_content="Response", thread_id=self.conversation_id
                )

            async def start(self):
                pass

        return ConcreteMemoryMixin(max_tokens=100)

    def test_init(self, memory_mixin):
        """Test initialisation of ConversationHistoryMixin."""
        assert memory_mixin.memory == []
        assert memory_mixin.max_history_tokens == 100
        assert memory_mixin.conversation_id is None

    @pytest.mark.asyncio
    async def test_remember(self, memory_mixin):
        """Test remembering a message."""
        message = MessageDict(role="user", content="Hello")
        await memory_mixin.remember(message)
        assert memory_mixin.memory == [message]

    @patch("assistants.ai.memory.ConversationHistoryMixin._get_token_count")
    def test_truncate_memory(self, mock_get_token_count, memory_mixin):
        """Test truncating memory when it exceeds the maximum token limit."""
        # Setup memory with multiple messages
        memory_mixin.memory = [
            MessageDict(role="user", content="Message 1"),
            MessageDict(role="assistant", content="Response 1"),
            MessageDict(role="user", content="Message 2"),
        ]

        # First call returns a value exceeding max_history_tokens, second call is below
        mock_get_token_count.side_effect = [150, 80]

        memory_mixin.truncate_memory()

        # Should have removed the first message
        assert len(memory_mixin.memory) == 2
        assert memory_mixin.memory[0]["content"] == "Response 1"

    @pytest.mark.asyncio
    async def test_load_conversation_with_id(self, memory_mixin):
        """Test loading a conversation with a specific ID."""
        conversation = Conversation(
            id="test-id",
            last_updated=datetime.now(),
        )

        # Patch the ConversationsTable.get method directly
        with patch(
            "assistants.user_data.sqlite_backend.conversations.ConversationsTable.get",
            return_value=conversation,
        ):
            await memory_mixin.load_conversation("test-id")

            assert memory_mixin.memory == []
            assert memory_mixin.conversation_id == "test-id"

    @pytest.mark.asyncio
    async def test_load_conversation_without_id(self, memory_mixin):
        """Test loading the last conversation when no ID is provided."""
        conversation = Conversation(
            id="last-id",
            last_updated=datetime.now(),
        )

        # Patch the ConversationsTable.get_last_conversation method directly
        with patch(
            "assistants.user_data.sqlite_backend.conversations.ConversationsTable.get_last_conversation",
            return_value=conversation,
        ):
            await memory_mixin.load_conversation()

            assert memory_mixin.memory == []
            assert memory_mixin.conversation_id == "last-id"

    @pytest.mark.asyncio
    async def test_get_last_message(self, memory_mixin):
        """Test getting the last message from the conversation."""
        memory_mixin.memory = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        memory_mixin.conversation_id = "test-id"

        result = await memory_mixin.get_last_message("any-thread-id")

        assert result.text_content == "Hi there"
        assert result.thread_id == "test-id"

    @pytest.mark.asyncio
    async def test_get_last_message_empty_memory(self, memory_mixin):
        """Test getting the last message from an empty conversation."""
        memory_mixin.memory = []

        result = await memory_mixin.get_last_message("any-thread-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_async_get_conversation_id_existing(self, memory_mixin):
        """Test getting an existing conversation ID."""
        memory_mixin.conversation_id = "existing-id"

        result = await memory_mixin.async_get_conversation_id()

        assert result == "existing-id"

    @pytest.mark.asyncio
    async def test_async_get_conversation_id_none(self, memory_mixin):
        """Test getting a conversation ID when none exists."""
        memory_mixin.conversation_id = None

        # Create a mock for load_conversation that sets the conversation_id
        async def mock_load_conversation(*args, **kwargs):
            memory_mixin.conversation_id = "loaded-id"

        # Patch the load_conversation method
        with patch.object(
            memory_mixin, "load_conversation", side_effect=mock_load_conversation
        ):
            # Call the method under test
            result = await memory_mixin.async_get_conversation_id()

            # Verify the result
            assert result == "loaded-id"

    @pytest.mark.asyncio
    async def test_get_whole_thread(self, memory_mixin):
        """Test getting the whole thread of messages."""
        memory_mixin.memory = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        result = await memory_mixin.get_whole_thread()

        assert result == memory_mixin.memory

    def test_get_token_count(self, memory_mixin):
        """Test getting the token count of the memory."""
        memory_mixin.memory = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        # The exact token count will depend on the encoding, but it should be > 0
        assert memory_mixin._get_token_count() > 0
