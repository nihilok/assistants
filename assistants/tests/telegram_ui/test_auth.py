"""
Unit tests for the telegram_ui.auth module.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from telegram import Update, Chat, User

from assistants.telegram_ui.auth import (
    restricted_access,
    requires_superuser,
    chat_data,
)
from assistants.user_data.interfaces.telegram_chat_data import NotAuthorised


class MockUpdate:
    """Mock Update object for testing auth decorators."""

    def __init__(self, chat_id: int = 12345, user_id: int = 67890):
        self.update_id = 1

        # Create mock user
        self.effective_user = Mock(spec=User)
        self.effective_user.id = user_id

        # Create mock chat
        self.effective_chat = Mock(spec=Chat)
        self.effective_chat.id = chat_id


class TestRestrictedAccess:
    """Test the restricted_access decorator."""

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_restricted_access_chat_authorized(self, mock_chat_data):
        """Test restricted access with authorized chat."""
        mock_chat_data.check_chat_authorised = AsyncMock()

        @restricted_access
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate()
        result = await dummy_handler(update, "context")

        mock_chat_data.check_chat_authorised.assert_called_once_with(12345)
        assert result == "success"

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_restricted_access_chat_not_authorized_user_authorized(self, mock_chat_data):
        """Test restricted access with unauthorized chat but authorized user."""
        mock_chat_data.check_chat_authorised = AsyncMock(side_effect=NotAuthorised())
        mock_chat_data.check_user_authorised = AsyncMock()

        @restricted_access
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate()
        result = await dummy_handler(update, "context")

        mock_chat_data.check_chat_authorised.assert_called_once_with(12345)
        mock_chat_data.check_user_authorised.assert_called_once_with(67890)
        assert result == "success"

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_restricted_access_chat_not_authorized_no_user(self, mock_chat_data):
        """Test restricted access with unauthorized chat and no effective user."""
        mock_chat_data.check_chat_authorised = AsyncMock(side_effect=NotAuthorised())

        @restricted_access
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate()
        update.effective_user = None

        with pytest.raises(NotAuthorised):
            await dummy_handler(update, "context")

        mock_chat_data.check_chat_authorised.assert_called_once_with(12345)
        mock_chat_data.check_user_authorised.assert_not_called()

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_restricted_access_both_not_authorized(self, mock_chat_data):
        """Test restricted access with both chat and user unauthorized."""
        mock_chat_data.check_chat_authorised = AsyncMock(side_effect=NotAuthorised())
        mock_chat_data.check_user_authorised = AsyncMock(side_effect=NotAuthorised())

        @restricted_access
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate()

        with pytest.raises(NotAuthorised):
            await dummy_handler(update, "context")

        mock_chat_data.check_chat_authorised.assert_called_once_with(12345)
        mock_chat_data.check_user_authorised.assert_called_once_with(67890)


class TestRequiresSuperuser:
    """Test the requires_superuser decorator."""

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_requires_superuser_success_first_arg(self, mock_chat_data):
        """Test requires_superuser when Update is first argument."""
        mock_chat_data.check_superuser = AsyncMock()

        @requires_superuser
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate()
        result = await dummy_handler(update, "context")

        mock_chat_data.check_superuser.assert_called_once_with(67890)
        assert result == "success"

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_requires_superuser_success_second_arg(self, mock_chat_data):
        """Test requires_superuser when Update is second argument."""
        mock_chat_data.check_superuser = AsyncMock()

        @requires_superuser
        async def dummy_handler(context, update):
            return "success"

        update = MockUpdate()
        result = await dummy_handler("context", update)

        mock_chat_data.check_superuser.assert_called_once_with(67890)
        assert result == "success"

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_requires_superuser_success_kwarg(self, mock_chat_data):
        """Test requires_superuser when Update is a keyword argument."""
        mock_chat_data.check_superuser = AsyncMock()

        @requires_superuser
        async def dummy_handler(context, **kwargs):
            return "success"

        update = MockUpdate()
        result = await dummy_handler("context", update=update)

        mock_chat_data.check_superuser.assert_called_once_with(67890)
        assert result == "success"

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_requires_superuser_no_update_found(self, mock_chat_data):
        """Test requires_superuser when no Update object is found."""
        @requires_superuser
        async def dummy_handler(context):
            return "success"

        with pytest.raises(ValueError, match="Update object not found in arguments"):
            await dummy_handler("context")

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_requires_superuser_not_authorized(self, mock_chat_data):
        """Test requires_superuser when user is not a superuser."""
        mock_chat_data.check_superuser = AsyncMock(side_effect=NotAuthorised())

        @requires_superuser
        async def dummy_handler(update, context):
            return "success"

        update = MockUpdate()

        with pytest.raises(NotAuthorised):
            await dummy_handler(update, "context")

        mock_chat_data.check_superuser.assert_called_once_with(67890)


class TestChatDataIntegration:
    """Test integration with chat_data singleton."""

    def test_chat_data_singleton(self):
        """Test that chat_data is properly initialized."""
        from assistants.telegram_ui.auth import chat_data
        from assistants.user_data.sqlite_backend.telegram_chat_data import TelegramSqliteUserData

        assert isinstance(chat_data, TelegramSqliteUserData)

    @pytest.mark.asyncio
    @patch('assistants.telegram_ui.auth.chat_data')
    async def test_chat_data_methods_called(self, mock_chat_data):
        """Test that chat_data methods are called correctly in decorators."""
        mock_chat_data.check_chat_authorised = AsyncMock()
        mock_chat_data.check_superuser = AsyncMock()

        @restricted_access
        @requires_superuser
        async def combined_handler(update, context):
            return "success"

        update = MockUpdate()
        result = await combined_handler(update, "context")

        # Both decorators should call their respective methods
        mock_chat_data.check_superuser.assert_called_once_with(67890)
        mock_chat_data.check_chat_authorised.assert_called_once_with(12345)
        assert result == "success"
