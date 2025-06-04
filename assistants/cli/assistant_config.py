"""
This module contains dataclasses and functions for assistant configuration.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from assistants.ai.types import ThinkingConfig


@dataclass
class AssistantParams:
    """Parameters for creating an assistant."""

    model: str
    max_history_tokens: int
    max_response_tokens: int
    thinking: ThinkingConfig
    instructions: Optional[str] = None
    tools: Optional[List[Dict[str, str]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary, excluding None values."""
        result = {
            "model": self.model,
            "max_history_tokens": self.max_history_tokens,
            "max_response_tokens": self.max_response_tokens,
            "thinking": self.thinking,
        }

        if self.instructions is not None:
            result["instructions"] = self.instructions

        if self.tools is not None:
            result["tools"] = self.tools

        return result
