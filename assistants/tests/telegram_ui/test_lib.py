"""
Unit tests for the telegram_ui.lib module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from telegram import Chat, User, Bot
from telegram._message import Message

from assistants.telegram_ui.lib import (
    update_has_effective_chat,
    update_has_message,
    requires_effective_chat,
    requires_message,
    requires_reply_to_message,
    build_telegram_specific_instructions,
    build_assistant_params,
    get_telegram_assistant,
    AssistantRegistry,
)


class MockUpdate:
    """Mock Update object for testing."""

    def __init__(
        self,
        has_chat: bool = True,
        has_message: bool = True,
        has_reply: bool = False,
        chat_id: int = 12345,
        user_id: int = 67890,
    ):
        self.update_id = 1

        if has_chat:
            self.effective_chat = Mock(spec=Chat)
            self.effective_chat.id = chat_id
        else:
            self.effective_chat = None  # type: ignore

        if has_message:
            self.message = Mock(spec=Message)
            self.message.from_user = Mock(spec=User)
            self.message.from_user.id = user_id

            if has_reply:
                self.message.reply_to_message = Mock(spec=Message)
                self.message.reply_to_message.from_user = Mock(spec=User)
                self.message.reply_to_message.from_user.id = 99999
            else:
                self.message.reply_to_message = None
        else:
            self.message = None  # type: ignore

        self.effective_message = self.message

        self.effective_user = Mock(spec=User)
        self.effective_user.id = user_id


class MockContext:
    """Mock Context object for testing."""

    def __init__(self):
        self.bot = Mock(spec=Bot)
        self.bot.send_message = AsyncMock()


class TestProtocolAndTypeGuards:
    """Test the StandardUpdate protocol and type guard functions."""

    def test_update_has_effective_chat_true(self):
        """Test update_has_effective_chat with valid chat."""
        update = MockUpdate(has_chat=True)
        assert update_has_effective_chat(update) is True  # type: ignore

    def test_update_has_effective_chat_false(self):
        """Test update_has_effective_chat with no chat."""
        update = MockUpdate(has_chat=False)
        assert update_has_effective_chat(update) is False  # type: ignore

    def test_update_has_message_true(self):
        """Test update_has_message with valid message."""
        update = MockUpdate(has_message=True)
        assert update_has_message(update) is True  # type: ignore

    def test_update_has_message_false(self):
        """Test update_has_message with no message."""
        update = MockUpdate(has_message=False)
        assert update_has_message(update) is False  # type: ignore


class TestDecorators:
    """Test the decorator functions."""

    @pytest.mark.asyncio
    async def test_requires_effective_chat_success(self):
        """Test requires_effective_chat with valid chat."""

        @requires_effective_chat
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_chat=True)
        context = MockContext()

        result = await dummy_handler(update, context)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_requires_effective_chat_no_chat(self):
        """Test requires_effective_chat with no chat."""

        @requires_effective_chat
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_chat=False)
        context = MockContext()

        result = await dummy_handler(update, context)
        assert result is None

    @pytest.mark.asyncio
    async def test_requires_message_success(self):
        """Test requires_message with valid message."""

        @requires_message
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_message=True)
        context = MockContext()

        result = await dummy_handler(update, context)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_requires_message_no_message(self):
        """Test requires_message with no message."""

        @requires_message
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_message=False)
        context = MockContext()

        result = await dummy_handler(update, context)
        assert result is None

    @pytest.mark.asyncio
    async def test_requires_reply_to_message_success(self):
        """Test requires_reply_to_message with valid reply."""

        @requires_reply_to_message
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_chat=True, has_message=True, has_reply=True)
        context = MockContext()

        result = await dummy_handler(update, context)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_requires_reply_to_message_no_reply(self):
        """Test requires_reply_to_message with no reply."""

        @requires_reply_to_message
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_chat=True, has_message=True, has_reply=False)
        context = MockContext()

        result = await dummy_handler(update, context)

        assert result is None
        context.bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="You must reply to a message from the target user to use this command",
        )

    @pytest.mark.asyncio
    async def test_requires_reply_to_message_no_chat(self):
        """Test requires_reply_to_message with no chat."""

        @requires_reply_to_message
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_chat=False, has_message=True, has_reply=True)
        context = MockContext()

        result = await dummy_handler(update, context)
        assert result is None

    @pytest.mark.asyncio
    async def test_requires_reply_to_message_no_message(self):
        """Test requires_reply_to_message with no message."""

        @requires_reply_to_message
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate(has_chat=True, has_message=False, has_reply=False)
        context = MockContext()

        result = await dummy_handler(update, context)
        assert result is None


class TestInstructionBuilding:
    """Test instruction and configuration building functions."""

    @patch("assistants.telegram_ui.lib.environment")
    def test_build_telegram_specific_instructions(self, mock_environment):
        """Test building telegram-specific instructions."""
        mock_environment.ASSISTANT_INSTRUCTIONS = "Base instructions"

        instructions = build_telegram_specific_instructions()

        assert "Base instructions" in instructions
        assert "All messages are prefixed with the name of the user" in instructions
        assert "you should not prefix your responses with your own name" in instructions

    @patch("assistants.telegram_ui.lib.environment")
    def test_build_telegram_specific_instructions_with_bot_info(self, mock_environment):
        """Test that bot username/name are included when provided."""
        mock_environment.ASSISTANT_INSTRUCTIONS = "Base instructions"

        instructions = build_telegram_specific_instructions("@jeeves", "Jeeves")

        assert "@jeeves" in instructions
        assert "Jeeves" in instructions

    @patch("assistants.telegram_ui.lib.environment")
    @patch("assistants.telegram_ui.lib.ThinkingConfig")
    def test_build_assistant_params(self, mock_thinking_config, mock_environment):
        """Test building assistant parameters."""
        mock_environment.DEFAULT_MAX_RESPONSE_TOKENS = 1000
        mock_environment.DEFAULT_MAX_HISTORY_TOKENS = 5000
        mock_environment.ASSISTANT_INSTRUCTIONS = "Test instructions"

        mock_thinking = Mock()
        mock_thinking_config.get_thinking_config.return_value = mock_thinking

        params = build_assistant_params("test-model")

        assert params.model == "test-model"
        assert params.max_history_tokens == 5000
        assert params.max_response_tokens == 1000
        assert params.thinking == mock_thinking
        assert "Test instructions" in params.instructions
        assert params.tools == [{"type": "code_interpreter"}, {"type": "web_search"}]

        mock_thinking_config.get_thinking_config.assert_called_once_with(0, 1000)

    @patch("assistants.telegram_ui.lib.environment")
    @patch("assistants.telegram_ui.lib.UniversalAssistant")
    def test_get_telegram_assistant(self, mock_universal_assistant, mock_environment):
        """Test getting telegram assistant instance."""
        mock_environment.DEFAULT_MODEL = "test-model"
        mock_environment.DEFAULT_MAX_RESPONSE_TOKENS = 1000
        mock_environment.DEFAULT_MAX_HISTORY_TOKENS = 5000
        mock_environment.ASSISTANT_INSTRUCTIONS = "Test instructions"

        mock_assistant_instance = Mock()
        mock_universal_assistant.return_value = mock_assistant_instance

        with patch("assistants.telegram_ui.lib.ThinkingConfig") as mock_thinking_config:
            mock_thinking = Mock()
            mock_thinking_config.get_thinking_config.return_value = mock_thinking

            assistant = get_telegram_assistant()

            assert assistant == mock_assistant_instance
            mock_universal_assistant.assert_called_once()

            # Check that the assistant was created with correct parameters
            call_kwargs = mock_universal_assistant.call_args[1]
            assert call_kwargs["model"] == "test-model"
            assert call_kwargs["max_history_tokens"] == 5000
            assert call_kwargs["max_response_tokens"] == 1000


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_decorator_with_extra_args(self):
        """Test decorators with extra positional arguments."""

        @requires_effective_chat
        async def handler_with_args(update, context, extra_arg1, extra_arg2):
            return f"success-{extra_arg1}-{extra_arg2}"

        update = MockUpdate(has_chat=True)
        context = MockContext()

        result = await handler_with_args(update, context, "arg1", "arg2")
        assert result == "success-arg1-arg2"

    @pytest.mark.asyncio
    async def test_decorator_with_kwargs(self):
        """Test decorators with keyword arguments."""

        @requires_message
        async def handler_with_kwargs(update, context, **kwargs):
            return f"success-{kwargs.get('test_arg', 'default')}"

        update = MockUpdate(has_message=True)
        context = MockContext()

        result = await handler_with_kwargs(update, context, test_arg="value")
        assert result == "success-value"

    def test_standard_update_protocol_properties(self):
        """Test that StandardUpdate protocol properties work correctly."""
        update = MockUpdate()

        # These should work if the mock is set up correctly
        assert hasattr(update, "update_id")
        assert hasattr(update, "effective_chat")
        assert hasattr(update, "message")
        assert hasattr(update, "effective_message")
        assert hasattr(update, "effective_user")

    @patch("assistants.telegram_ui.lib.environment")
    def test_build_instructions_with_empty_base(self, mock_environment):
        """Test building instructions with empty base instructions."""
        mock_environment.ASSISTANT_INSTRUCTIONS = ""

        instructions = build_telegram_specific_instructions()

        # Should still contain the telegram-specific part
        assert "All messages are prefixed with the name of the user" in instructions

    @pytest.mark.asyncio
    async def test_multiple_decorators_combination(self):
        """Test combining multiple decorators."""

        @requires_effective_chat
        @requires_message
        async def multi_decorated_handler(update, context):
            return "all-checks-passed"

        # Test with valid update
        update = MockUpdate(has_chat=True, has_message=True)
        context = MockContext()
        result = await multi_decorated_handler(update, context)
        assert result == "all-checks-passed"

        # Test with invalid chat
        update = MockUpdate(has_chat=False, has_message=True)
        result = await multi_decorated_handler(update, context)
        assert result is None

        # Test with invalid message
        update = MockUpdate(has_chat=True, has_message=False)
        result = await multi_decorated_handler(update, context)
        assert result is None


class TestAssistantRegistry:
    """Test the per-chat AssistantRegistry."""

    @patch("assistants.telegram_ui.lib.get_telegram_assistant")
    def test_get_creates_instance_on_first_call(self, mock_factory):
        """registry.get creates a new assistant for an unseen chat_id."""
        mock_factory.return_value = Mock()
        reg = AssistantRegistry()

        assistant = reg.get(111, "@bot", "Bot")

        mock_factory.assert_called_once_with("@bot", "Bot")
        assert assistant is mock_factory.return_value

    @patch("assistants.telegram_ui.lib.get_telegram_assistant")
    def test_get_returns_cached_instance(self, mock_factory):
        """registry.get returns the same instance on subsequent calls."""
        mock_factory.return_value = Mock()
        reg = AssistantRegistry()

        a1 = reg.get(111, "@bot", "Bot")
        a2 = reg.get(111, "@bot", "Bot")

        assert a1 is a2
        mock_factory.assert_called_once()  # only created once

    @patch("assistants.telegram_ui.lib.get_telegram_assistant")
    def test_get_creates_separate_instances_per_chat(self, mock_factory):
        """Different chat_ids get separate assistant instances."""
        mock_factory.side_effect = [Mock(), Mock()]
        reg = AssistantRegistry()

        a1 = reg.get(111)
        a2 = reg.get(222)

        assert a1 is not a2
        assert mock_factory.call_count == 2

    @patch("assistants.telegram_ui.lib.get_telegram_assistant")
    def test_reset_removes_instance(self, mock_factory):
        """reset evicts the cached instance so the next get creates a fresh one."""
        first = Mock()
        second = Mock()
        mock_factory.side_effect = [first, second]
        reg = AssistantRegistry()

        a1 = reg.get(111)
        reg.reset(111)
        a2 = reg.get(111)

        assert a1 is first
        assert a2 is second
        assert mock_factory.call_count == 2

    def test_reset_nonexistent_chat_is_safe(self):
        """reset on an unknown chat_id does not raise."""
        reg = AssistantRegistry()
        reg.reset(999)  # should not raise
