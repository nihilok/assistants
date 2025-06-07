import asyncio
from unittest.mock import MagicMock, patch

import pytest

from assistants.ai.openai import (
    OpenAIAssistant,
    OpenAICompletion,
    ReasoningModelMixin,
    is_valid_thinking_level,
)
from assistants.ai.types import ThinkingConfig
from assistants.lib.exceptions import ConfigError


class TestReasoningModelMixin:
    """Tests for the ReasoningModelMixin class."""

    @pytest.fixture
    def reasoning_mixin(self):
        """Create a concrete implementation of ReasoningModelMixin for testing."""

        class ConcreteReasoningMixin(ReasoningModelMixin):
            def __init__(self, model, thinking):
                self.model = model
                self.tools = None
                self.reasoning_model_init(thinking)

        return ConcreteReasoningMixin

    def test_reasoning_model_init_non_reasoning_model(self, reasoning_mixin):
        """Test initialisation with a non-reasoning model."""
        mixin = reasoning_mixin("non-reasoning-model", ThinkingConfig(1))
        assert not hasattr(mixin, "reasoning")

    def test_reasoning_model_init_reasoning_model(self, reasoning_mixin):
        """Test initialisation with a reasoning model."""
        with patch.object(ReasoningModelMixin, "REASONING_MODELS", ["reasoning-model"]):
            mixin = reasoning_mixin("reasoning-model", ThinkingConfig(1))
            assert mixin.reasoning == {"effort": "medium"}

    def test_reasoning_model_init_with_tools(self, reasoning_mixin):
        """Test initialisation with tools."""
        with patch.object(ReasoningModelMixin, "REASONING_MODELS", ["reasoning-model"]):
            mixin = reasoning_mixin(
                "reasoning-model", ThinkingConfig.get_thinking_config(1)
            )
            mixin.tools = ["tool1", "tool2"]
            mixin.reasoning_model_init(ThinkingConfig(1))
            from openai._types import NOT_GIVEN

            assert mixin.tools is NOT_GIVEN

    def test_set_reasoning_effort_valid(self, reasoning_mixin):
        """Test setting reasoning effort with valid thinking level."""
        with patch.object(ReasoningModelMixin, "REASONING_MODELS", ["reasoning-model"]):
            mixin = reasoning_mixin("reasoning-model", ThinkingConfig(0))
            assert mixin.reasoning == {"effort": "low"}

            mixin = reasoning_mixin("reasoning-model", ThinkingConfig(1))
            assert mixin.reasoning == {"effort": "medium"}

            mixin = reasoning_mixin("reasoning-model", ThinkingConfig(2))
            assert mixin.reasoning == {"effort": "high"}

    def test_set_reasoning_effort_invalid(self, reasoning_mixin):
        """Test setting reasoning effort with invalid thinking level."""
        with patch.object(ReasoningModelMixin, "REASONING_MODELS", ["reasoning-model"]):
            with pytest.raises(ConfigError):
                reasoning_mixin("reasoning-model", ThinkingConfig(3))

            with pytest.raises(ConfigError):
                reasoning_mixin("reasoning-model", ThinkingConfig(-1))

            with pytest.raises(ConfigError):
                reasoning_mixin("reasoning-model", ThinkingConfig("invalid"))  # type: ignore


class TestAssistant:
    """Tests for the Assistant class."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        client = MagicMock()
        client.responses.create.return_value = MagicMock(output_text="AI response")
        return client

    @pytest.fixture
    def assistant(self, mock_openai_client):
        """Create an Assistant instance for testing."""
        with patch("openai.OpenAI", return_value=mock_openai_client):
            return OpenAIAssistant(
                model="gpt-4",
                instructions="You are a helpful assistant.",
                api_key="test-key",
            )

    def test_init(self, assistant, mock_openai_client):
        """Test initial of Assistant."""
        assert assistant.model == "gpt-4"
        assert assistant.instructions == "You are a helpful assistant."
        assert assistant.client == mock_openai_client
        # We don't test reasoning here as it depends on the model and REASONING_MODELS

    def test_init_missing_api_key(self):
        """Test initial with missing API key."""
        with pytest.raises(ConfigError):
            with patch("assistants.ai.openai.environment.OPENAI_API_KEY", ""):
                OpenAIAssistant(
                    model="gpt-4",
                    instructions="You are a helpful assistant.",
                    api_key="",
                )

    @pytest.mark.asyncio
    async def test_start(self, assistant):
        """Test starting the assistant."""
        await assistant.start()
        assert assistant.memory == [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        assert assistant.last_message is None

    @pytest.mark.asyncio
    async def test_start_with_existing_memory(self, assistant):
        """Test starting the assistant with existing memory."""
        assistant.memory = [{"role": "user", "content": "Hello"}]
        await assistant.start()
        assert assistant.memory == [{"role": "user", "content": "Hello"}]
        assert assistant.last_message is None

    def test_assistant_id(self, assistant):
        """Test getting the assistant ID."""
        assert assistant.assistant_id == assistant.config_hash

    def test_config_hash(self, assistant):
        """Test getting the configuration hash."""
        # First call should generate the hash
        hash1 = assistant.config_hash
        assert hash1 is not None

        # Second call should return the cached hash
        hash2 = assistant.config_hash
        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_prompt(self, assistant, mock_openai_client):
        """Test sending a prompt to the assistant."""
        response = await assistant.prompt("Hello")

        assert assistant.last_prompt == "Hello"
        mock_openai_client.responses.create.assert_called_once()
        assert response == mock_openai_client.responses.create.return_value

        # Check that the message was added to memory
        assert assistant.memory[-2] == {"role": "user", "content": "Hello"}
        assert assistant.memory[-1] == {"role": "assistant", "content": "AI response"}

    @pytest.mark.asyncio
    async def test_image_prompt(self, assistant, mock_openai_client):
        """Test sending an image prompt to the assistant."""
        mock_openai_client.images.generate.return_value = MagicMock(
            data=[MagicMock(url="https://example.com/image.png")]
        )

        url = await assistant.image_prompt("Generate an image of a cat")

        assert assistant.last_prompt == "Generate an image of a cat"
        mock_openai_client.images.generate.assert_called_once()
        assert url == "https://example.com/image.png"

    @pytest.mark.asyncio
    async def test_converse(self, assistant, mock_openai_client):
        """Test conversing with the assistant."""
        result = await assistant.converse("Hello")

        assert result.text_content == "AI response"
        # The thread_id could be an empty string or None depending on the implementation
        assert result.thread_id is not None
        assert assistant.last_message == {"role": "assistant", "content": "AI response"}

    @pytest.mark.asyncio
    async def test_converse_empty_input(self, assistant):
        """Test conversing with empty input."""
        result = await assistant.converse("")

        assert result is None

    @pytest.mark.asyncio
    @patch("assistants.ai.openai.OpenAIAssistant.load_conversation")
    async def test_converse_with_thread_id(self, mock_load_conversation, assistant):
        """Test conversing with a thread ID."""
        await assistant.converse("Hello", "thread-id")

        mock_load_conversation.assert_called_once_with("thread-id")


class TestCompletion:
    """Tests for the Completion class."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        client = MagicMock()
        message = MagicMock(content="AI response")
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=message)]
        )
        return client

    @pytest.fixture
    def completion(self, mock_openai_client):
        """Create a Completion instance for testing."""
        with patch("openai.OpenAI", return_value=mock_openai_client):
            return OpenAICompletion(model="gpt-4", api_key="test-key")

    def test_init(self, completion, mock_openai_client):
        """Test initial of Completion."""
        assert completion.model == "gpt-4"
        assert completion.client == mock_openai_client
        # We don't test reasoning here as it depends on the model and REASONING_MODELS

    def test_init_missing_api_key(self):
        """Test initial with missing API key."""
        with pytest.raises(ConfigError):
            with patch("assistants.ai.openai.environment.OPENAI_API_KEY", ""):
                OpenAICompletion(model="gpt-4", api_key="")

    @pytest.mark.asyncio
    async def test_start(self, completion):
        """Test starting the completion."""
        await completion.start()
        # start() is a no-op for Completion

    def test_complete(self, completion, mock_openai_client):
        """Test completing a prompt."""
        message = asyncio.run(completion.complete("Hello"))

        mock_openai_client.chat.completions.create.assert_called_once()
        assert message.content == "AI response"

        # Check that the messages were added to memory
        assert completion.memory[-2] == {"role": "user", "content": "Hello"}
        assert completion.memory[-1] == {"role": "assistant", "content": "AI response"}

    @pytest.mark.asyncio
    async def test_converse(self, completion):
        """Test conversing with the completion."""
        with patch.object(completion, "complete") as mock_complete:
            mock_complete.return_value = MagicMock(content="AI response")

            result = await completion.converse("Hello")

            mock_complete.assert_called_once_with("Hello")
            assert result.text_content == "AI response"
            assert result.thread_id == completion.conversation_id

    @pytest.mark.asyncio
    async def test_converse_empty_input(self, completion):
        """Test conversing with empty input."""
        result = await completion.converse("")

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_audio(self, completion, mock_openai_client):
        """Test completing an audio prompt."""
        with patch("base64.b64decode") as mock_b64decode, \
             patch.object(completion, "remember", return_value=None) as mock_remember:
            mock_b64decode.return_value = b"audio data"

            # Create a proper structure for the mock response
            message_mock = MagicMock()
            message_mock.content = "Transcribed audio"
            message_mock.audio = MagicMock()
            message_mock.audio.data = "base64data"
            message_mock.audio.id = "audio-id"

            mock_openai_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=message_mock)]
            )

            result = await completion.complete_audio("Hello")

            mock_openai_client.chat.completions.create.assert_called_once()
            mock_b64decode.assert_called_once_with("base64data")
            assert result == b"audio data"

    @pytest.mark.asyncio
    async def test_complete_audio_empty_input(self, completion):
        """Test completing an audio prompt with empty input."""
        result = await completion.complete_audio("")

        assert result is None


def test_is_valid_thinking_level():
    """Test the is_valid_thinking_level function."""
    assert is_valid_thinking_level(0) is True
    assert is_valid_thinking_level(1) is True
    assert is_valid_thinking_level(2) is True
    assert is_valid_thinking_level(3) is False
    assert is_valid_thinking_level(-1) is False
    assert is_valid_thinking_level("invalid") is False  # type: ignore
