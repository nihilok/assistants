import random
import pytest
from unittest.mock import patch

from bot.cli import cli
from bot.exceptions import NoResponseError


class MockText:
    value: str = "Hello!"


class MockContent:
    text: MockText = MockText()


class MockMessage:
    content = [MockContent()]

    def __init__(self, _id=None, thread_id=None):
        self.id = _id or self.random_id()
        self.thread_id = thread_id or self.random_id()

    @staticmethod
    def random_id():
        return str(random.randint(10000, 99999))


@pytest.mark.parametrize("exit_keyword", ["q", "Q", "quit", "QUIT", "Quit", "quiT"])
def test_exit_keywords_exit_the_program(exit_keyword):
    with patch(
        "bot.ai.assistant.Assistant.converse",
        return_value=MockMessage(thread_id="123"),
    ) as mock_converse:
        with patch("builtins.input", lambda *args: exit_keyword):
            cli()
        assert not mock_converse.called


@patch("builtins.input", lambda *args: "Hello!")
def test_conversation_does_not_get_stuck_in_loop_if_final_message_doesnt_change():
    with patch(
        "bot.ai.assistant.Assistant.converse",
        return_value=MockMessage(_id="1"),
    ) as mock_converse:
        with pytest.raises(NoResponseError):
            cli()
        assert mock_converse.call_count == 2
