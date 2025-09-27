import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from assistants.ai.universal import UniversalAssistant


@pytest.mark.asyncio
async def test_universal_image_prompt():
    # Mock the UniversalLLMClient inside UniversalAssistant instance
    with patch("assistants.ai.universal.UniversalLLMClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Prepare a fake image response structure
        image_resp = MagicMock()
        img_obj = MagicMock()
        img_obj.b64_json = "base64imgdata"
        image_resp.images = [img_obj]
        mock_client.generate_image = AsyncMock(return_value=image_resp)

        assistant = UniversalAssistant(model="gpt-image-1", api_key="dummy")
        result = await assistant.image_prompt("A cat sitting on a sofa")

        mock_client.generate_image.assert_awaited_once()
        assert result == "base64imgdata"


@pytest.mark.asyncio
async def test_universal_image_prompt_no_images():
    with patch("assistants.ai.universal.UniversalLLMClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        image_resp = MagicMock()
        image_resp.images = []
        mock_client.generate_image = AsyncMock(return_value=image_resp)

        assistant = UniversalAssistant(model="gpt-image-1", api_key="dummy")
        result = await assistant.image_prompt("A landscape")
        assert result is None
