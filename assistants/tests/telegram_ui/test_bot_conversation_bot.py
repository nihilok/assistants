"""
Unit tests for the telegram_ui.bot_conversation_bot module.
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram import Bot
from telegram.ext import Application

from assistants.telegram_ui.bot_conversation_bot import (
    MessageRecord,
    BotConversationManager,
    ConversationBot,
    MainConversationBot,
    SecondaryConversationBot,
    DEFAULT_CONVERSATION_BOT_INSTRUCTIONS,
)


class TestMessageRecord:
    """Test the MessageRecord class."""

    def test_message_record_creation(self):
        """Test MessageRecord creation with all parameters."""
        timestamp = time.time()
        record = MessageRecord("bot_1", 12345, "Hello world", timestamp)

        assert record.bot_id == "bot_1"
        assert record.user_id == 12345
        assert record.text == "Hello world"
        assert record.timestamp == timestamp

    def test_message_record_creation_no_timestamp(self):
        """Test MessageRecord creation without timestamp."""
        record = MessageRecord("user", 67890, "Test message")

        assert record.bot_id == "user"
        assert record.user_id == 67890
        assert record.text == "Test message"
        assert isinstance(record.timestamp, float)
        assert record.timestamp > 0

    def test_to_dict(self):
        """Test MessageRecord to_dict conversion."""
        timestamp = 1234567890.0
        record = MessageRecord("bot_2", 11111, "Test", timestamp)

        result = record.to_dict()
        expected = {
            "bot_id": "bot_2",
            "user_id": 11111,
            "text": "Test",
            "timestamp": timestamp,
        }
        assert result == expected

    def test_from_dict(self):
        """Test MessageRecord from_dict creation."""
        data = {
            "bot_id": "bot_3",
            "user_id": 22222,
            "text": "From dict",
            "timestamp": 9876543210.0,
        }

        record = MessageRecord.from_dict(data)
        assert record.bot_id == "bot_3"
        assert record.user_id == 22222
        assert record.text == "From dict"
        assert record.timestamp == 9876543210.0


class TestBotConversationManager:
    """Test the BotConversationManager class."""

    @pytest.fixture
    def manager(self):
        """Fixture providing a mocked BotConversationManager."""
        with patch(
            "assistants.telegram_ui.bot_conversation_bot.get_telegram_data"
        ) as mock_get_data:
            mock_get_data.return_value.db_path = ":memory:"
            manager = BotConversationManager()
            manager.bot_conversations_table = AsyncMock()
            return manager

    @pytest.mark.asyncio
    async def test_initialize(self, manager):
        """Test manager initialization."""
        with patch(
            "assistants.telegram_ui.bot_conversation_bot.init_db"
        ) as mock_init_db:

            async def mock_init():
                return None

            mock_init_db.return_value = mock_init()
            manager.bot_conversations_table.create_table = AsyncMock()

            await manager.initialize()

            mock_init_db.assert_called_once()
            manager.bot_conversations_table.create_table.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chat_data(self, manager):
        """Test getting chat data."""
        # Mock database message
        mock_db_msg = Mock()
        mock_db_msg.bot_id = "bot_1"
        mock_db_msg.user_id = 12345
        mock_db_msg.text = "Hello"
        mock_db_msg.timestamp = 1234567890.0

        manager.bot_conversations_table.get_chat_messages = AsyncMock(
            return_value=[mock_db_msg]
        )

        result = await manager.get_chat_data(12345)

        assert len(result) == 1
        assert isinstance(result[0], MessageRecord)
        assert result[0].bot_id == "bot_1"
        assert result[0].user_id == 12345
        assert result[0].text == "Hello"
        assert result[0].timestamp == 1234567890.0

        manager.bot_conversations_table.get_chat_messages.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_get_messages_since_last_bot_response(self, manager):
        """Test getting messages since last bot response."""
        mock_db_msg1 = Mock()
        mock_db_msg1.bot_id = "user"
        mock_db_msg1.user_id = 12345
        mock_db_msg1.text = "User message"
        mock_db_msg1.timestamp = 1234567890.0

        mock_db_msg2 = Mock()
        mock_db_msg2.bot_id = "user"
        mock_db_msg2.user_id = 67890
        mock_db_msg2.text = "Another user message"
        mock_db_msg2.timestamp = 1234567900.0

        manager.bot_conversations_table.get_messages_since_last_bot_response = (
            AsyncMock(return_value=[mock_db_msg1, mock_db_msg2])
        )

        result = await manager.get_messages_since_last_bot_response(12345, "bot_1")

        assert len(result) == 2
        assert result[0].text == "User message"
        assert result[1].text == "Another user message"

        manager.bot_conversations_table.get_messages_since_last_bot_response.assert_called_once_with(
            12345, "bot_1"
        )

    @pytest.mark.asyncio
    async def test_add_message(self, manager):
        """Test adding a message."""
        with patch("assistants.telegram_ui.bot_conversation_bot.logger") as mock_logger:
            manager.bot_conversations_table.insert = AsyncMock()

            message = MessageRecord("bot_1", 12345, "Test message", 1234567890.0)
            await manager.add_message(12345, message)

            mock_logger.info.assert_called_once_with(
                "Adding message to chat 12345: Test message"
            )
            manager.bot_conversations_table.insert.assert_called_once()

            # Check the inserted message
            inserted_msg = manager.bot_conversations_table.insert.call_args[0][0]
            assert inserted_msg.chat_id == 12345
            assert inserted_msg.bot_id == "bot_1"
            assert inserted_msg.user_id == 12345
            assert inserted_msg.text == "Test message"
            assert inserted_msg.timestamp == 1234567890.0

    @pytest.mark.asyncio
    async def test_get_last_message(self, manager):
        """Test getting the last message."""
        mock_db_msg = Mock()
        mock_db_msg.bot_id = "user"
        mock_db_msg.user_id = 12345
        mock_db_msg.text = "Last message"
        mock_db_msg.timestamp = 1234567890.0

        manager.bot_conversations_table.get_last_message = AsyncMock(
            return_value=mock_db_msg
        )

        result = await manager.get_last_message(12345)

        assert isinstance(result, MessageRecord)
        assert result.bot_id == "user"
        assert result.user_id == 12345
        assert result.text == "Last message"
        assert result.timestamp == 1234567890.0

        manager.bot_conversations_table.get_last_message.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_get_last_message_none(self, manager):
        """Test getting last message when none exists."""
        manager.bot_conversations_table.get_last_message = AsyncMock(return_value=None)

        result = await manager.get_last_message(12345)

        assert result is None


class TestConversationBot:
    """Test the ConversationBot base class."""

    @pytest.fixture
    def mock_manager(self):
        """Fixture providing a mock BotConversationManager."""
        return Mock(spec=BotConversationManager)

    @pytest.fixture
    def mock_assistant(self):
        """Fixture providing a mock assistant."""
        assistant = Mock()
        assistant.converse = AsyncMock()
        assistant.memory = Mock()
        assistant.memory.extend = Mock()
        return assistant

    @pytest.fixture
    def conversation_bot(self, mock_manager, mock_assistant):
        """Fixture providing a ConversationBot instance."""
        with patch(
            "assistants.telegram_ui.bot_conversation_bot.Application"
        ) as mock_app_class:
            mock_builder = Mock()
            mock_app_class.builder.return_value = mock_builder
            mock_builder.token.return_value = mock_builder

            mock_application = Mock(spec=Application)
            mock_builder.build.return_value = mock_application

            mock_bot = Mock(spec=Bot)
            mock_bot.id = 98765
            mock_application.bot = mock_bot

            bot = ConversationBot(
                token="test_token",
                manager=mock_manager,
                assistant=mock_assistant,
                bot_id="test_bot",
                response_interval=(5, 10),
            )
            return bot

    def test_conversation_bot_initialization(
        self, conversation_bot, mock_manager, mock_assistant
    ):
        """Test ConversationBot initialization."""
        assert conversation_bot.token == "test_token"
        assert conversation_bot.manager == mock_manager
        assert conversation_bot.assistant == mock_assistant
        assert conversation_bot.bot_id == "test_bot"
        assert conversation_bot.response_interval == (5, 10)
        assert conversation_bot.active_chats == set()

    @pytest.mark.asyncio
    async def test_start_responding(self, conversation_bot):
        """Test starting response loop for a chat."""
        with patch.object(conversation_bot, "_response_loop") as mock_response_loop:

            async def mock_loop():
                return None

            mock_response_loop.return_value = mock_loop()

            await conversation_bot.start_responding(12345)

            assert 12345 in conversation_bot.active_chats

    @pytest.mark.asyncio
    async def test_start_responding_already_active(self, conversation_bot):
        """Test starting response loop for already active chat."""
        conversation_bot.active_chats.add(12345)

        with patch.object(conversation_bot, "_response_loop") as mock_response_loop:
            await conversation_bot.start_responding(12345)

            mock_response_loop.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_responding(self, conversation_bot):
        """Test stopping response loop for a chat."""
        conversation_bot.active_chats.add(12345)

        await conversation_bot.stop_responding(12345)

        assert 12345 not in conversation_bot.active_chats

    @pytest.mark.asyncio
    async def test_maybe_respond_no_last_message(self, conversation_bot, mock_manager):
        """Test _maybe_respond with no last message."""
        mock_manager.get_last_message = AsyncMock(return_value=None)

        await conversation_bot._maybe_respond(12345)

        mock_manager.get_last_message.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_maybe_respond_own_message(self, conversation_bot, mock_manager):
        """Test _maybe_respond with bot's own message."""
        last_message = MessageRecord("test_bot", 12345, "Bot message", time.time())
        mock_manager.get_last_message = AsyncMock(return_value=last_message)

        with patch.object(conversation_bot, "_generate_response") as mock_generate:
            await conversation_bot._maybe_respond(12345)

            mock_generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_maybe_respond_success(self, conversation_bot, mock_manager):
        """Test successful _maybe_respond."""
        last_message = MessageRecord("user", 12345, "User message", time.time())
        mock_manager.get_last_message = AsyncMock(return_value=last_message)
        mock_manager.add_message = AsyncMock()

        with patch.object(conversation_bot, "_generate_response") as mock_generate:
            # Mock _generate_response to return a string directly when awaited
            mock_generate.return_value = "Bot response"
            conversation_bot.bot.send_message = AsyncMock()

            with patch("time.strftime") as mock_strftime:
                mock_strftime.return_value = "2023-01-01 12:00:00"

                await conversation_bot._maybe_respond(12345)

                conversation_bot.bot.send_message.assert_called_once_with(
                    chat_id=12345, text="Bot response"
                )
                mock_manager.add_message.assert_called_once()

                # Check the recorded message
                recorded_message = mock_manager.add_message.call_args[0][1]
                assert recorded_message.bot_id == "test_bot"
                assert recorded_message.user_id == 98765
                assert (
                    '{"user": "test_bot", "time": "2023-01-01 12:00:00"} Bot response'
                    in recorded_message.text
                )

    @pytest.mark.asyncio
    async def test_generate_response_no_recent_messages(
        self, conversation_bot, mock_manager
    ):
        """Test _generate_response with no recent messages."""
        mock_manager.get_messages_since_last_bot_response = AsyncMock(return_value=[])

        last_message = MessageRecord("user", 12345, "User message", time.time())
        result = await conversation_bot._generate_response(12345, last_message)

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_response_with_memory(
        self, conversation_bot, mock_manager, mock_assistant
    ):
        """Test _generate_response with assistant memory."""
        recent_messages = [
            MessageRecord("user", 12345, "Message 1", time.time()),
            MessageRecord("user", 67890, "Message 2", time.time()),
        ]
        mock_manager.get_messages_since_last_bot_response = AsyncMock(
            return_value=recent_messages
        )

        mock_response = Mock()
        mock_response.text_content = "Generated response"
        mock_assistant.converse = AsyncMock(return_value=mock_response)

        last_message = MessageRecord("user", 12345, "Latest message", time.time())
        result = await conversation_bot._generate_response(12345, last_message)

        assert result == "Generated response"
        mock_assistant.memory.extend.assert_called_once()
        mock_assistant.converse.assert_called_once_with(
            "Latest message", "12345-test_bot"
        )

    @pytest.mark.asyncio
    async def test_generate_response_no_memory(self, conversation_bot, mock_manager):
        """Test _generate_response without assistant memory."""
        # Remove memory attribute
        if hasattr(conversation_bot.assistant, "memory"):
            delattr(conversation_bot.assistant, "memory")

        recent_messages = [MessageRecord("user", 12345, "Message", time.time())]
        mock_manager.get_messages_since_last_bot_response = AsyncMock(
            return_value=recent_messages
        )

        mock_response = Mock()
        mock_response.text_content = "Response without memory"
        conversation_bot.assistant.converse = AsyncMock(return_value=mock_response)

        last_message = MessageRecord("user", 12345, "Latest message", time.time())
        result = await conversation_bot._generate_response(12345, last_message)

        assert result == "Response without memory"
        conversation_bot.assistant.converse.assert_called_once_with(
            "Latest message", "12345-test_bot"
        )

    @pytest.mark.asyncio
    async def test_start_and_stop(self, conversation_bot):
        """Test bot start and stop methods."""
        conversation_bot.application.initialize = AsyncMock()
        conversation_bot.application.start = AsyncMock()
        conversation_bot.application.stop = AsyncMock()
        conversation_bot.application.shutdown = AsyncMock()

        # Mock updater
        mock_updater = Mock()
        mock_updater.start_polling = AsyncMock()
        conversation_bot.application.updater = mock_updater

        await conversation_bot.start()

        conversation_bot.application.initialize.assert_called_once()
        conversation_bot.application.start.assert_called_once()

        await conversation_bot.stop()

        conversation_bot.application.stop.assert_called_once()
        conversation_bot.application.shutdown.assert_called_once()


class TestMainConversationBot:
    """Test the MainConversationBot class."""

    @pytest.fixture
    def main_bot(self):
        """Fixture providing a MainConversationBot instance."""
        with patch(
            "assistants.telegram_ui.bot_conversation_bot.Application"
        ) as mock_app_class:
            mock_builder = Mock()
            mock_app_class.builder.return_value = mock_builder
            mock_builder.token.return_value = mock_builder

            mock_application = Mock(spec=Application)
            mock_application.add_handler = Mock()
            mock_builder.build.return_value = mock_application

            mock_bot = Mock(spec=Bot)
            mock_bot.id = 98765
            mock_application.bot = mock_bot

            mock_manager = Mock(spec=BotConversationManager)
            mock_assistant = Mock()

            bot = MainConversationBot(
                token="main_token",
                manager=mock_manager,
                assistant=mock_assistant,
                bot_id="main_bot",
            )
            return bot

    def test_setup_handlers(self, main_bot):
        """Test that MainConversationBot sets up handlers correctly."""
        # Check that add_handler was called 3 times (start, stop, message)
        assert main_bot.application.add_handler.call_count == 3

        # Get the handlers
        handlers = [
            call[0][0] for call in main_bot.application.add_handler.call_args_list
        ]

        # Check that we have the expected number of handlers
        assert len(handlers) == 3

        # All handlers should have a commands attribute (for CommandHandler) or filters (for MessageHandler)
        # CommandHandlers have commands list, MessageHandlers have filters
        command_handlers = [
            h for h in handlers if hasattr(h, "commands") and h.commands
        ]
        message_handlers = [
            h
            for h in handlers
            if hasattr(h, "filters") and h.filters and not hasattr(h, "commands")
        ]

        # Should have 2 command handlers (start, stop) and 1 message handler
        assert len(command_handlers) == 2  # start and stop commands
        assert len(message_handlers) == 1  # message handler

    @pytest.mark.asyncio
    async def test_start_command(self, main_bot):
        """Test the /start command handler."""
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_chat = Mock()
        mock_update.effective_chat.id = 12345
        mock_update.effective_user = Mock()
        mock_update.effective_user.id = 67890
        mock_update.message = Mock()
        mock_update.message.reply_text = AsyncMock()

        mock_context = Mock()
        mock_context.bot = Mock()
        mock_context.bot.username = "test_main_bot"

        with patch("assistants.telegram_ui.auth.chat_data") as mock_chat_data:
            mock_chat_data.check_superuser = AsyncMock()

            with patch.object(main_bot, "start_responding") as mock_start_responding:
                mock_start_responding.return_value = AsyncMock(return_value=None)()

                await main_bot._start_command(mock_update, mock_context)

                assert main_bot.bot_id == "test_main_bot"
                mock_start_responding.assert_called_once_with(12345)
                mock_update.message.reply_text.assert_called_once_with(
                    "Bot test_main_bot is active. Type /stop to deactivate."
                )

    @pytest.mark.asyncio
    async def test_start_command_no_chat(self, main_bot):
        """Test /start command with no effective chat."""
        mock_update = Mock()
        mock_update.effective_chat = None
        mock_update.effective_user = Mock()
        mock_update.effective_user.id = 67890
        mock_context = Mock()

        with patch("assistants.telegram_ui.auth.chat_data") as mock_chat_data:
            mock_chat_data.check_superuser = AsyncMock()

            with patch(
                "assistants.telegram_ui.bot_conversation_bot.logger"
            ) as mock_logger:
                await main_bot._start_command(mock_update, mock_context)

                mock_logger.warning.assert_called_once_with(
                    "Received a command without a chat."
                )

    @pytest.mark.asyncio
    async def test_stop_command(self, main_bot):
        """Test the /stop command handler."""
        mock_update = Mock()
        mock_update.effective_chat = Mock()
        mock_update.effective_chat.id = 12345
        mock_update.message = Mock()
        mock_update.message.reply_text = AsyncMock()

        mock_context = Mock()

        with patch.object(main_bot, "stop_responding") as mock_stop_responding:

            async def mock_stop():
                return None

            mock_stop_responding.return_value = mock_stop()

            await main_bot._stop_command(mock_update, mock_context)

            mock_stop_responding.assert_called_once_with(12345)
            mock_update.message.reply_text.assert_called_once_with(
                "Bot main_bot is now inactive. Type /start to reactivate."
            )

    @pytest.mark.asyncio
    async def test_message_handler(self, main_bot):
        """Test the message handler."""
        mock_update = Mock()
        mock_update.effective_chat = Mock()
        mock_update.effective_chat.id = 12345
        mock_update.effective_user = Mock()
        mock_update.effective_user.id = 67890
        mock_update.effective_user.username = "testuser"
        mock_update.message = Mock()
        mock_update.message.text = "Hello world"

        with patch.object(main_bot, "start_responding") as mock_start_responding:

            async def mock_start():
                return None

            mock_start_responding.return_value = mock_start()

            with patch("time.strftime") as mock_strftime:
                mock_strftime.return_value = "2023-01-01 12:00:00"

                await main_bot._message_handler(mock_update, Mock())

                main_bot.manager.add_message.assert_called_once()

                # Check the recorded message
                chat_id, message = main_bot.manager.add_message.call_args[0]
                assert chat_id == 12345
                assert message.bot_id == "user"
                assert message.user_id == 67890
                assert (
                    '{"user": "testuser", "time": "2023-01-01 12:00:00"} Hello world'
                    in message.text
                )

                mock_start_responding.assert_called_once_with(12345)


class TestSecondaryConversationBot:
    """Test the SecondaryConversationBot class."""

    @pytest.fixture
    def secondary_bot(self):
        """Fixture providing a SecondaryConversationBot instance."""
        with patch(
            "assistants.telegram_ui.bot_conversation_bot.Application"
        ) as mock_app_class:
            mock_builder = Mock()
            mock_app_class.builder.return_value = mock_builder
            mock_builder.token.return_value = mock_builder

            mock_application = Mock(spec=Application)
            mock_application.add_handler = Mock()
            mock_builder.build.return_value = mock_application

            mock_bot = Mock(spec=Bot)
            mock_application.bot = mock_bot

            mock_manager = Mock(spec=BotConversationManager)
            mock_assistant = Mock()

            bot = SecondaryConversationBot(
                token="secondary_token",
                manager=mock_manager,
                assistant=mock_assistant,
                bot_id="secondary_bot",
            )
            return bot

    def test_setup_handlers(self, secondary_bot):
        """Test that SecondaryConversationBot sets up only command handlers."""
        # Check that add_handler was called 2 times (start and stop only)
        assert secondary_bot.application.add_handler.call_count == 2

        # Get the handlers
        handlers = [
            call[0][0] for call in secondary_bot.application.add_handler.call_args_list
        ]

        # Check that all are command handlers
        command_handlers = [
            h for h in handlers if hasattr(h, "commands") and h.commands
        ]
        assert len(command_handlers) == 2  # start and stop commands only

    @pytest.mark.asyncio
    async def test_start_command(self, secondary_bot):
        """Test the /start command handler for secondary bot."""
        mock_update = Mock()
        mock_update.effective_chat = Mock()
        mock_update.effective_chat.id = 12345
        mock_update.effective_user = Mock()
        mock_update.effective_user.id = 67890
        mock_update.message = Mock()
        mock_update.message.reply_text = AsyncMock()

        mock_context = Mock()
        mock_context.bot = Mock()
        mock_context.bot.username = "test_secondary_bot"

        # Patch the correct chat_data import path as used in the code
        with patch("assistants.telegram_ui.auth.chat_data") as mock_chat_data:
            mock_chat_data.check_superuser = AsyncMock()

            with patch.object(
                secondary_bot, "start_responding"
            ) as mock_start_responding:
                mock_start_responding.return_value = AsyncMock(return_value=None)()

                with patch(
                    "assistants.telegram_ui.bot_conversation_bot.logger"
                ) as mock_logger:
                    await secondary_bot._start_command(mock_update, mock_context)

                    assert secondary_bot.bot_id == "test_secondary_bot"
                    mock_logger.info.assert_called_once_with(
                        "Starting bot test_secondary_bot for chat 12345"
                    )
                    mock_start_responding.assert_called_once_with(12345)
                    mock_update.message.reply_text.assert_called_once_with(
                        "Bot test_secondary_bot is now active. Type /stop to deactivate."
                    )


class TestConstants:
    """Test module constants and configurations."""

    def test_default_conversation_bot_instructions(self):
        """Test that default instructions are properly defined."""
        assert isinstance(DEFAULT_CONVERSATION_BOT_INSTRUCTIONS, str)
        assert len(DEFAULT_CONVERSATION_BOT_INSTRUCTIONS) > 0
        assert "Telegram" in DEFAULT_CONVERSATION_BOT_INSTRUCTIONS
        assert "conversation bot" in DEFAULT_CONVERSATION_BOT_INSTRUCTIONS.lower()


class TestIntegration:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.bot_conversation_bot.os.environ.get")
    @patch("assistants.telegram_ui.bot_conversation_bot.sys.argv")
    async def test_main_function_setup(self, mock_argv, mock_env_get):
        """Test the main function setup."""
        mock_argv.__getitem__.return_value = ["bot_a", "bot_b"]
        mock_env_get.side_effect = lambda key: {
            "MAIN_BOT_TOKEN": "main_token",
            "SECONDARY_BOT_TOKEN": "secondary_token",
        }.get(key)

        with patch(
            "assistants.telegram_ui.bot_conversation_bot.BotConversationManager"
        ) as mock_manager_class:
            mock_manager = Mock()
            mock_manager.initialize = AsyncMock()
            mock_manager_class.return_value = mock_manager

            with patch(
                "assistants.telegram_ui.bot_conversation_bot.MainConversationBot"
            ) as mock_main_bot_class:
                with patch(
                    "assistants.telegram_ui.bot_conversation_bot.SecondaryConversationBot"
                ) as mock_secondary_bot_class:
                    mock_main_bot = Mock()
                    mock_main_bot.start = AsyncMock()
                    mock_main_bot.stop = AsyncMock()
                    mock_main_bot_class.return_value = mock_main_bot

                    mock_secondary_bot = Mock()
                    mock_secondary_bot.start = AsyncMock()
                    mock_secondary_bot.stop = AsyncMock()
                    mock_secondary_bot_class.return_value = mock_secondary_bot

                    from assistants.telegram_ui.bot_conversation_bot import main

                    # Test initialization part of main function
                    # We can't easily test the infinite loop, so we'll test the setup
                    try:
                        # This will run until the while loop, then we'll interrupt
                        task = asyncio.create_task(main())
                        await asyncio.sleep(0.01)  # Let it start
                        task.cancel()
                        await asyncio.gather(task, return_exceptions=True)
                    except asyncio.CancelledError:
                        pass

                    # Verify setup was called
                    mock_manager.initialize.assert_called_once()
                    mock_main_bot.start.assert_called_once()
                    mock_secondary_bot.start.assert_called_once()
