"""
Unit tests for the telegram_ui.tg_bot module.
"""

import pytest
from unittest.mock import Mock, patch
from telegram.ext import Application, CommandHandler, MessageHandler

from assistants.telegram_ui.tg_bot import build_bot, run_polling


class TestBuildBot:
    """Test the build_bot function."""

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    @patch("assistants.telegram_ui.tg_bot.logger")
    def test_build_bot_success(self, mock_logger, mock_app_builder):
        """Test successful bot building with all handlers."""
        # Mock the application builder chain
        mock_builder = Mock()
        mock_app_builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder

        mock_application = Mock(spec=Application)
        mock_builder.build.return_value = mock_application

        token = "test_token_123"
        result = build_bot(token)

        # Verify the builder chain
        mock_app_builder.assert_called_once()
        mock_builder.token.assert_called_once_with(token)
        mock_builder.build.assert_called_once()

        # Verify all command handlers are added
        expected_commands = [
            "add_chat",
            "remove_chat",
            "add_user",
            "remove_user",
            "promote",
            "demote",
            "new_thread",
            "auto_reply",
            "image",
            "voice",
            "unfinished_business",
        ]

        # Check that add_handler was called for each command + message handler
        assert mock_application.add_handler.call_count == len(expected_commands) + 1

        # Verify command handlers
        command_calls = mock_application.add_handler.call_args_list[:-1]
        for i, command in enumerate(expected_commands):
            handler = command_calls[i][0][0]
            assert isinstance(handler, CommandHandler)
            assert handler.commands == {command}

        # Verify message handler (last call)
        message_handler_call = mock_application.add_handler.call_args_list[-1]
        message_handler = message_handler_call[0][0]
        assert isinstance(message_handler, MessageHandler)

        # Verify setup completion log
        mock_logger.info.assert_called_once_with("Setup complete!")

        assert result == mock_application

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    def test_build_bot_with_different_token(self, mock_app_builder):
        """Test build_bot with different token values."""
        mock_builder = Mock()
        mock_app_builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_application = Mock(spec=Application)
        mock_builder.build.return_value = mock_application

        tokens = ["token1", "very_long_token_with_numbers_123456", ""]

        for token in tokens:
            build_bot(token)
            mock_builder.token.assert_called_with(token)

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    def test_build_bot_handler_functions_imported(self, mock_app_builder):
        """Test that all handler functions are properly imported and used."""
        mock_builder = Mock()
        mock_app_builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_application = Mock(spec=Application)
        mock_builder.build.return_value = mock_application

        # Import the handlers to verify they exist
        from assistants.telegram_ui.commands import (
            clear_pending_buttons,
            promote_user,
            demote_user,
            authorise_chat,
            authorise_user,
            deauthorise_chat,
            deauthorise_user,
            new_thread,
            toggle_auto_reply,
            message_handler,
            generate_image,
            respond_voice,
        )

        build_bot("test_token")

        # Verify that add_handler was called with actual function objects
        calls = mock_application.add_handler.call_args_list

        # Extract the handlers from the calls
        handlers = [call[0][0] for call in calls]
        command_handlers = [h for h in handlers if isinstance(h, CommandHandler)]
        message_handlers = [h for h in handlers if isinstance(h, MessageHandler)]

        # Verify we have the expected number of handlers
        assert len(command_handlers) == 11  # 11 command handlers
        assert len(message_handlers) == 1  # 1 message handler

        # Verify the command handlers have the correct callbacks
        expected_handlers = {
            "add_chat": authorise_chat,
            "remove_chat": deauthorise_chat,
            "add_user": authorise_user,
            "remove_user": deauthorise_user,
            "promote": promote_user,
            "demote": demote_user,
            "new_thread": new_thread,
            "auto_reply": toggle_auto_reply,
            "image": generate_image,
            "voice": respond_voice,
            "unfinished_business": clear_pending_buttons,
        }

        # Check that each command handler has the correct callback
        for handler in command_handlers:
            command = list(handler.commands)[0]  # Get the command name
            if command in expected_handlers:
                assert handler.callback == expected_handlers[command]

        # Check message handler
        assert message_handlers[0].callback == message_handler


class TestRunPolling:
    """Test the run_polling function."""

    @patch("assistants.telegram_ui.tg_bot.logger")
    def test_run_polling_success(self, mock_logger):
        """Test successful polling run."""
        mock_application = Mock(spec=Application)
        mock_application.run_polling = Mock()

        run_polling(mock_application)

        mock_logger.info.assert_called_once_with("Telegram bot is running...")
        mock_application.run_polling.assert_called_once()

    @patch("assistants.telegram_ui.tg_bot.logger")
    def test_run_polling_with_exception(self, mock_logger):
        """Test polling run with exception."""
        mock_application = Mock(spec=Application)
        mock_application.run_polling = Mock(side_effect=Exception("Connection error"))

        with pytest.raises(Exception, match="Connection error"):
            run_polling(mock_application)

        mock_logger.info.assert_called_once_with("Telegram bot is running...")
        mock_application.run_polling.assert_called_once()


class TestIntegration:
    """Test integration scenarios."""

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    @patch("assistants.telegram_ui.tg_bot.logger")
    def test_full_bot_setup_and_run(self, mock_logger, mock_app_builder):
        """Test full bot setup and run scenario."""
        # Setup mocks
        mock_builder = Mock()
        mock_app_builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder

        mock_application = Mock(spec=Application)
        mock_builder.build.return_value = mock_application
        mock_application.run_polling = Mock()

        # Build and run bot
        bot = build_bot("integration_test_token")
        run_polling(bot)

        # Verify complete flow
        mock_app_builder.assert_called_once()
        mock_builder.token.assert_called_once_with("integration_test_token")
        mock_builder.build.assert_called_once()

        # Verify handlers were added
        assert mock_application.add_handler.call_count == 12  # 11 commands + 1 message

        # Verify logging
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call("Setup complete!")
        mock_logger.info.assert_any_call("Telegram bot is running...")

        # Verify polling started
        mock_application.run_polling.assert_called_once()

        assert bot == mock_application


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    def test_build_bot_builder_exception(self, mock_app_builder):
        """Test build_bot when ApplicationBuilder raises exception."""
        mock_app_builder.side_effect = Exception("Builder failed")

        with pytest.raises(Exception, match="Builder failed"):
            build_bot("test_token")

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    def test_build_bot_token_exception(self, mock_app_builder):
        """Test build_bot when token() raises exception."""
        mock_builder = Mock()
        mock_app_builder.return_value = mock_builder
        mock_builder.token.side_effect = Exception("Invalid token")

        with pytest.raises(Exception, match="Invalid token"):
            build_bot("invalid_token")

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    def test_build_bot_build_exception(self, mock_app_builder):
        """Test build_bot when build() raises exception."""
        mock_builder = Mock()
        mock_app_builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.side_effect = Exception("Build failed")

        with pytest.raises(Exception, match="Build failed"):
            build_bot("test_token")

    @patch("assistants.telegram_ui.tg_bot.ApplicationBuilder")
    def test_build_bot_add_handler_exception(self, mock_app_builder):
        """Test build_bot when add_handler raises exception."""
        mock_builder = Mock()
        mock_app_builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder

        mock_application = Mock(spec=Application)
        mock_application.add_handler.side_effect = Exception("Handler failed")
        mock_builder.build.return_value = mock_application

        with pytest.raises(Exception, match="Handler failed"):
            build_bot("test_token")
