"""
Comprehensive unit tests for the telegram_ui.commands module.
"""

from unittest.mock import AsyncMock, patch, Mock
from typing import Optional

import pytest
from telegram import Bot, Chat, Message, User, ReplyKeyboardRemove
from telegram.constants import ParseMode

from assistants.telegram_ui.commands import (
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
    clear_pending_buttons,
)
from assistants.user_data.interfaces.telegram_chat_data import ChatData


# Mock the auth system at module level to bypass authorization checks in tests
@pytest.fixture(autouse=True)
def mock_auth_system():
    """Automatically mock the authorization system for all tests."""
    with patch("assistants.telegram_ui.auth.chat_data") as mock_chat_data:
        # Mock the authorization check methods to always succeed
        mock_chat_data.check_chat_authorised = AsyncMock()
        mock_chat_data.check_user_authorised = AsyncMock()
        yield mock_chat_data


class MockUpdate:
    """Mock Update object for testing."""

    def __init__(
        self,
        chat_id: int = 12345,
        user_id: int = 67890,
        message_text: Optional[str] = None,
        reply_to_message: Optional[Message] = None,
        bot_username: str = "test_bot",
        bot_name: str = "TestBot",
        bot_id: int = 98765,
    ):
        self.update_id = 1

        # Create mock user
        self.effective_user = Mock(spec=User)
        self.effective_user.id = user_id
        self.effective_user.first_name = "TestUser"

        # Create mock chat
        self.effective_chat = Mock(spec=Chat)
        self.effective_chat.id = chat_id

        # Create mock message
        self.message = Mock(spec=Message)
        self.message.text = message_text
        self.message.from_user = self.effective_user
        self.message.reply_to_message = reply_to_message

        # Create mock reply_to_message if needed
        if reply_to_message:
            self.message.reply_to_message = reply_to_message

        self.effective_message = self.message


class MockContext:
    """Mock Context object for testing."""

    def __init__(
        self,
        bot_username: str = "test_bot",
        bot_name: str = "TestBot",
        bot_id: int = 98765,
    ):
        self.bot = Mock(spec=Bot)
        self.bot.username = bot_username
        self.bot.first_name = bot_name
        self.bot.id = bot_id
        self.bot.send_message = AsyncMock()
        self.bot.send_voice = AsyncMock()


@pytest.fixture
def mock_update():
    """Fixture providing a mock update object."""
    return MockUpdate()


@pytest.fixture
def mock_context():
    """Fixture providing a mock context object."""
    return MockContext()


@pytest.fixture
def mock_reply_to_message():
    """Fixture providing a mock reply_to_message."""
    reply_msg = Mock(spec=Message)
    reply_msg.from_user = Mock(spec=User)
    reply_msg.from_user.id = 99999
    return reply_msg


class TestUserManagementCommands:
    """Test user promotion/demotion and authorization commands."""

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.auth.chat_data")
    async def test_promote_user_success(
        self, mock_auth_chat_data, mock_chat_data, mock_reply_to_message
    ):
        """Test successful user promotion."""
        update = MockUpdate(reply_to_message=mock_reply_to_message)
        update.message.reply_to_message = mock_reply_to_message
        context = MockContext()

        mock_chat_data.promote_superuser = AsyncMock()
        mock_auth_chat_data.check_superuser = AsyncMock()

        await promote_user(update, context)

        mock_chat_data.promote_superuser.assert_called_once_with(99999)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="User promoted"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.auth.chat_data")
    async def test_demote_user_success(
        self, mock_auth_chat_data, mock_chat_data, mock_reply_to_message
    ):
        """Test successful user demotion."""
        update = MockUpdate(reply_to_message=mock_reply_to_message)
        update.message.reply_to_message = mock_reply_to_message
        context = MockContext()

        mock_chat_data.demote_superuser = AsyncMock()
        mock_auth_chat_data.check_superuser = AsyncMock()

        await demote_user(update, context)

        mock_chat_data.demote_superuser.assert_called_once_with(99999)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="User demoted"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.auth.chat_data", new_callable=AsyncMock)
    @patch("assistants.telegram_ui.commands.chat_data", new_callable=AsyncMock)
    async def test_authorise_chat_success(
        self, mock_commands_chat_data, mock_auth_chat_data
    ):
        """Test successful chat authorization."""
        update = MockUpdate()
        context = MockContext()

        mock_commands_chat_data.authorise_chat = AsyncMock()
        mock_auth_chat_data.check_superuser = AsyncMock()

        await authorise_chat(update, context)

        mock_commands_chat_data.authorise_chat.assert_called_once_with(12345)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Chat authorised"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.auth.chat_data")
    async def test_authorise_user_success(
        self, mock_auth_chat_data, mock_chat_data, mock_reply_to_message
    ):
        """Test successful user authorization."""
        update = MockUpdate(reply_to_message=mock_reply_to_message)
        update.message.reply_to_message = mock_reply_to_message
        context = MockContext()

        mock_chat_data.authorise_chat = AsyncMock()
        mock_auth_chat_data.check_superuser = AsyncMock()

        await authorise_user(update, context)

        mock_chat_data.authorise_chat.assert_called_once_with(99999)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="User authorised"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.auth.chat_data", new_callable=AsyncMock)
    @patch("assistants.telegram_ui.commands.chat_data", new_callable=AsyncMock)
    async def test_deauthorise_chat_success(
        self, mock_commands_chat_data, mock_auth_chat_data
    ):
        """Test successful chat deauthorization."""
        update = MockUpdate()
        context = MockContext()

        mock_commands_chat_data.deauthorise_chat = AsyncMock()
        mock_auth_chat_data.check_superuser = AsyncMock()

        await deauthorise_chat(update, context)

        mock_commands_chat_data.deauthorise_chat.assert_called_once_with(12345)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Chat de-authorised"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.auth.chat_data")
    async def test_deauthorise_user_success(
        self, mock_auth_chat_data, mock_chat_data, mock_reply_to_message
    ):
        """Test successful user deauthorization."""
        update = MockUpdate(reply_to_message=mock_reply_to_message)
        update.message.reply_to_message = mock_reply_to_message
        context = MockContext()

        mock_chat_data.deauthorise_user = AsyncMock()
        mock_auth_chat_data.check_superuser = AsyncMock()

        await deauthorise_user(update, context)

        mock_chat_data.deauthorise_user.assert_called_once_with(99999)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="User de-authorised"
        )


class TestThreadManagement:
    """Test thread and conversation management commands."""

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.get_conversations_table")
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_new_thread_success(
        self, mock_assistant, mock_chat_data, mock_conversations_table
    ):
        """Test successful new thread creation."""
        update = MockUpdate()
        context = MockContext()

        mock_chat_data.clear_last_thread_id = AsyncMock()
        mock_table = AsyncMock()
        mock_conversations_table.return_value = mock_table
        mock_table.delete = AsyncMock()

        await new_thread(update, context)

        mock_chat_data.clear_last_thread_id.assert_called_once_with(12345)
        mock_table.delete.assert_called_once_with(id=12345)
        assert mock_assistant.last_message is None
        context.bot.send_message.assert_called_once_with(
            12345, "Conversation history cleared."
        )


class TestAutoReply:
    """Test auto-reply toggle functionality."""

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    async def test_toggle_auto_reply_turn_on(self, mock_chat_data):
        """Test turning auto-reply on."""
        update = MockUpdate(message_text="toggle")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(chat_id=12345, thread_id="test", auto_reply=False)
        )
        mock_chat_data.set_auto_reply = AsyncMock()

        await toggle_auto_reply(update, context)

        mock_chat_data.set_auto_reply.assert_called_once_with(12345, True)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Auto reply is ON"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    async def test_toggle_auto_reply_turn_off(self, mock_chat_data):
        """Test turning auto-reply off."""
        update = MockUpdate(message_text="toggle")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(chat_id=12345, thread_id="test", auto_reply=True)
        )
        mock_chat_data.set_auto_reply = AsyncMock()

        await toggle_auto_reply(update, context)

        mock_chat_data.set_auto_reply.assert_called_once_with(12345, False)
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Auto reply is OFF"
        )


class TestMessageHandler:
    """Test the main message handler functionality."""

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data", new_callable=AsyncMock)
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_message_handler_no_text(self, mock_assistant, mock_chat_data):
        """Test message handler with no text."""
        update = MockUpdate(message_text=None)
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock()

        result = await message_handler(update, context)

        assert result is None
        mock_chat_data.get_chat_data.assert_called_once_with(12345)

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_message_handler_auto_reply_enabled(
        self, mock_assistant, mock_chat_data
    ):
        """Test message handler with auto-reply enabled."""
        update = MockUpdate(message_text="Hello @test_bot")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(
                chat_id=12345, thread_id="existing_thread", auto_reply=True
            )
        )
        mock_chat_data.save_chat_data = AsyncMock()
        mock_assistant.load_conversation = AsyncMock()
        mock_assistant.converse = AsyncMock(
            return_value=Mock(text_content="Hello back!")
        )
        mock_assistant.conversation_id = "test_conversation_id"

        await message_handler(update, context)

        mock_assistant.load_conversation.assert_called_once_with("existing_thread")
        mock_assistant.converse.assert_called_once_with(
            "TestUser: Hello TestBot", "existing_thread"
        )
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Hello back!"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_message_handler_auto_reply_disabled_not_tagged(
        self, mock_assistant, mock_chat_data
    ):
        """Test message handler with auto-reply disabled and bot not tagged."""
        update = MockUpdate(message_text="Hello there")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(
                chat_id=12345, thread_id="existing_thread", auto_reply=False
            )
        )
        mock_assistant.remember = AsyncMock()

        await message_handler(update, context)

        mock_assistant.remember.assert_called_once()
        call_args = mock_assistant.remember.call_args[0][0]
        # Ensure call_args is a dict with 'role' and 'content' keys
        assert isinstance(call_args, dict)
        assert call_args["role"] == "user"
        assert call_args["content"] == "TestUser: Hello there"
        mock_assistant.converse.assert_not_called()

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_message_handler_reply_to_bot(self, mock_assistant, mock_chat_data):
        """Test message handler replying to bot message."""
        # Create a reply to message from the bot
        reply_msg = Mock(spec=Message)
        reply_msg.from_user = Mock(spec=User)
        reply_msg.from_user.id = 98765  # Bot's ID

        update = MockUpdate(message_text="Reply to bot")
        update.message.reply_to_message = reply_msg
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(
                chat_id=12345, thread_id="existing_thread", auto_reply=False
            )
        )
        mock_chat_data.save_chat_data = AsyncMock()
        mock_assistant.load_conversation = AsyncMock()
        mock_assistant.converse = AsyncMock(
            return_value=Mock(text_content="Bot response")
        )
        mock_assistant.conversation_id = "test_conversation_id"

        await message_handler(update, context)

        mock_assistant.converse.assert_called_once()
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Bot response"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_message_handler_no_response(self, mock_assistant, mock_chat_data):
        """Test message handler when assistant returns no response."""
        update = MockUpdate(message_text="Hello @test_bot")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(
                chat_id=12345, thread_id="existing_thread", auto_reply=True
            )
        )
        mock_assistant.load_conversation = AsyncMock()
        mock_assistant.converse = AsyncMock(return_value=None)

        await message_handler(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="No response."
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_message_handler_code_blocks(self, mock_assistant, mock_chat_data):
        """Test message handler with code blocks in response."""
        update = MockUpdate(message_text="Show me code")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(
                chat_id=12345, thread_id="existing_thread", auto_reply=True
            )
        )
        mock_assistant.load_conversation = AsyncMock()
        mock_assistant.converse = AsyncMock(
            return_value=Mock(
                text_content="Here's some code:\n```python\nprint('hello')\n```\nThat's it!"
            )
        )

        await message_handler(update, context)

        # Should send 3 messages: text before, code block, text after
        assert context.bot.send_message.call_count == 3
        calls = context.bot.send_message.call_args_list

        # First call: text before code
        assert calls[0][1]["text"] == "Here's some code:\n"

        # Second call: code block with markdown
        assert calls[1][1]["text"] == "```python\nprint('hello')\n```"
        assert calls[1][1]["parse_mode"] == ParseMode.MARKDOWN_V2

        # Third call: text after code
        assert calls[2][1]["text"] == "\nThat's it!"

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.chat_data")
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_message_handler_new_thread_creation(
        self, mock_assistant, mock_chat_data
    ):
        """Test message handler creating new thread when none exists."""
        update = MockUpdate(message_text="Hello")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(chat_id=12345, thread_id=None, auto_reply=True)
        )
        mock_chat_data.save_chat_data = AsyncMock()
        mock_assistant.load_conversation = AsyncMock()
        mock_assistant.converse = AsyncMock(return_value=Mock(text_content="Response"))
        mock_assistant.conversation_id = "new_conversation_id"

        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = "new_thread_id"

            await message_handler(update, context)

            mock_assistant.load_conversation.assert_called_once_with("new_thread_id")
            mock_chat_data.save_chat_data.assert_called_once()
            saved_data = mock_chat_data.save_chat_data.call_args[0][0]
            assert saved_data.thread_id == "new_conversation_id"


class TestImageGeneration:
    """Test image generation functionality."""

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_not_supported(self, mock_assistant):
        """Test image generation when not supported by assistant."""
        update = MockUpdate(message_text="/image test prompt")
        context = MockContext()

        # Remove image_prompt attribute to simulate unsupported feature
        if hasattr(mock_assistant, "image_prompt"):
            delattr(mock_assistant, "image_prompt")

        await generate_image(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="This assistant does not support image generation."
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_no_text(self, mock_assistant):
        """Test image generation with no message text."""
        update = MockUpdate(message_text=None)
        context = MockContext()

        mock_assistant.image_prompt = AsyncMock()

        result = await generate_image(update, context)

        assert result is None
        mock_assistant.image_prompt.assert_not_called()

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_empty_prompt(self, mock_assistant):
        """Test image generation with empty prompt."""
        update = MockUpdate(message_text="/image ")
        context = MockContext()

        mock_assistant.image_prompt = AsyncMock()

        await generate_image(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Please provide a prompt after /image"
        )
        mock_assistant.image_prompt.assert_not_called()

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_success_string(self, mock_assistant):
        """Test successful image generation with base64 string."""
        update = MockUpdate(message_text="/image sunset landscape")
        update.message.reply_photo = AsyncMock()
        context = MockContext()

        # Create a simple base64 encoded image (1x1 pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFBAixnwgAAAABJRU5ErkJggg=="
        mock_assistant.image_prompt = AsyncMock(return_value=test_image_b64)

        await generate_image(update, context)

        mock_assistant.image_prompt.assert_called_once_with("sunset landscape")
        update.message.reply_photo.assert_called_once()

        # Check that photo was sent with correct caption
        call_args = update.message.reply_photo.call_args
        assert call_args[1]["caption"] == "Prompt: sunset landscape"

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_success_data_uri(self, mock_assistant):
        """Test successful image generation with data URI."""
        update = MockUpdate(message_text="/image test")
        update.message.reply_photo = AsyncMock()
        context = MockContext()

        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFBAixnwgAAAABJRU5ErkJggg=="
        data_uri = f"data:image/png;base64,{test_image_b64}"
        mock_assistant.image_prompt = AsyncMock(return_value=data_uri)

        await generate_image(update, context)

        update.message.reply_photo.assert_called_once()

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_success_openai_format(self, mock_assistant):
        """Test successful image generation with OpenAI response format."""
        update = MockUpdate(message_text="/image test")
        update.message.reply_photo = AsyncMock()
        context = MockContext()

        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFBAixnwgAAAABJRU5ErkJggg=="
        openai_response = {"data": [{"b64_json": test_image_b64}]}
        mock_assistant.image_prompt = AsyncMock(return_value=openai_response)

        await generate_image(update, context)

        update.message.reply_photo.assert_called_once()

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_generation_failed(self, mock_assistant):
        """Test image generation failure."""
        update = MockUpdate(message_text="/image test")
        context = MockContext()

        mock_assistant.image_prompt = AsyncMock(side_effect=Exception("API Error"))

        await generate_image(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Image generation failed: API Error"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_invalid_base64(self, mock_assistant):
        """Test image generation with invalid base64."""
        update = MockUpdate(message_text="/image test")
        context = MockContext()

        mock_assistant.image_prompt = AsyncMock(return_value="invalid_base64!")

        await generate_image(update, context)

        context.bot.send_message.assert_called_once()
        assert (
            "Failed to decode image data"
            in context.bot.send_message.call_args[1]["text"]
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    async def test_generate_image_send_as_document_fallback(self, mock_assistant):
        """Test image generation fallback to document when photo fails."""
        update = MockUpdate(message_text="/image test")
        update.message.reply_photo = AsyncMock(side_effect=Exception("Photo failed"))
        update.message.reply_document = AsyncMock()
        context = MockContext()

        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFBAixnwgAAAABJRU5ErkJggg=="
        mock_assistant.image_prompt = AsyncMock(return_value=test_image_b64)

        await generate_image(update, context)

        update.message.reply_photo.assert_called_once()
        update.message.reply_document.assert_called_once()


class TestVoiceResponse:
    """Test voice response functionality."""

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    @patch("assistants.telegram_ui.commands.chat_data")
    async def test_respond_voice_not_supported(self, mock_chat_data, mock_assistant):
        """Test voice response when not supported by assistant."""
        update = MockUpdate(message_text="/voice test")
        context = MockContext()

        # Remove audio_response attribute to simulate unsupported feature
        if hasattr(mock_assistant, "audio_response"):
            delattr(mock_assistant, "audio_response")

        await respond_voice(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="This assistant does not support voice responses."
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    @patch("assistants.telegram_ui.commands.chat_data")
    async def test_respond_voice_no_text(self, mock_chat_data, mock_assistant):
        """Test voice response with no message text."""
        update = MockUpdate(message_text=None)
        context = MockContext()

        mock_assistant.audio_response = AsyncMock()
        mock_chat_data.get_chat_data = AsyncMock()

        result = await respond_voice(update, context)

        assert result is None
        mock_assistant.audio_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    @patch("assistants.telegram_ui.commands.chat_data")
    async def test_respond_voice_success_bytes(self, mock_chat_data, mock_assistant):
        """Test successful voice response with bytes."""
        update = MockUpdate(message_text="/voice hello")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(
                chat_id=12345, thread_id="existing_thread", auto_reply=True
            )
        )
        mock_chat_data.save_chat_data = AsyncMock()
        mock_assistant.audio_response = AsyncMock(return_value=b"audio_data")
        mock_assistant.conversation_id = "test_conversation_id"

        await respond_voice(update, context)

        mock_assistant.audio_response.assert_called_once_with(
            "hello", thread_id="existing_thread"
        )
        context.bot.send_voice.assert_called_once_with(
            chat_id=12345, voice=b"audio_data", caption="Response"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    @patch("assistants.telegram_ui.commands.chat_data")
    async def test_respond_voice_success_text(self, mock_chat_data, mock_assistant):
        """Test voice response returning text instead of audio."""
        update = MockUpdate(message_text="/voice hello")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(
                chat_id=12345, thread_id="existing_thread", auto_reply=True
            )
        )
        mock_assistant.audio_response = AsyncMock(return_value="Text response")

        await respond_voice(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Text response"
        )

    @pytest.mark.asyncio
    @patch("assistants.telegram_ui.commands.assistant")
    @patch("assistants.telegram_ui.commands.chat_data")
    async def test_respond_voice_new_thread(self, mock_chat_data, mock_assistant):
        """Test voice response creating new thread."""
        update = MockUpdate(message_text="/voice hello")
        context = MockContext()

        mock_chat_data.get_chat_data = AsyncMock(
            return_value=ChatData(chat_id=12345, thread_id=None, auto_reply=True)
        )
        mock_chat_data.save_chat_data = AsyncMock()
        mock_assistant.audio_response = AsyncMock(return_value=b"audio_data")
        mock_assistant.conversation_id = "new_conversation_id"

        await respond_voice(update, context)

        mock_chat_data.save_chat_data.assert_called_once()
        saved_data = mock_chat_data.save_chat_data.call_args[0][0]
        assert saved_data.thread_id == "new_conversation_id"


class TestClearPendingButtons:
    """Test clear pending buttons functionality."""

    @pytest.mark.asyncio
    async def test_clear_pending_buttons_success(self):
        """Test successful clearing of pending buttons."""
        update = MockUpdate()
        context = MockContext()

        await clear_pending_buttons(update, context)

        context.bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Removing keyboard...",
            reply_markup=ReplyKeyboardRemove(),
        )

    @pytest.mark.asyncio
    async def test_clear_pending_buttons_failure(self):
        """Test handling of failure in clearing pending buttons."""
        update = MockUpdate()
        context = MockContext()

        context.bot.send_message = AsyncMock(
            side_effect=[Exception("Network error"), None]
        )

        await clear_pending_buttons(update, context)

        # Should call send_message twice: first fails, second succeeds with error message
        assert context.bot.send_message.call_count == 2
        error_call = context.bot.send_message.call_args_list[1]
        assert "Failed to clear requests: Network error" in error_call[1]["text"]
