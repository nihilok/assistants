"""
MCP tool integration for AI assistants.

This module provides functionality to convert MCP tools to univllm format
and handle tool calls from the assistant.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from univllm import ToolDefinition  # type: ignore
from mcp.types import Tool as MCPTool

from assistants.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


def mcp_tool_to_univllm_tool(mcp_tool: MCPTool, server_name: str) -> ToolDefinition:
    """
    Convert an MCP tool to a univllm ToolDefinition.

    :param mcp_tool: The MCP tool to convert.
    :param server_name: Name of the server providing this tool.
    :return: A univllm ToolDefinition.
    """
    # Store server name in the tool name to track which server it belongs to
    tool_name = f"{server_name}__{mcp_tool.name}"

    return ToolDefinition(
        name=tool_name,
        description=mcp_tool.description or "",
        input_schema=mcp_tool.inputSchema,
    )


class MCPToolHandler:
    """Handles MCP tool integration for AI assistants."""

    def __init__(self, manager: Optional[MCPManager] = None):
        """
        Initialize the MCP tool handler.

        :param manager: Optional MCPManager instance. If None, creates a new one.
        """
        self.manager = manager or MCPManager()
        self._connected = False

    async def connect(self) -> None:
        """Connect to all configured MCP servers."""
        if not self._connected:
            await self.manager.connect_all()
            self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        if self._connected:
            await self.manager.disconnect_all()
            self._connected = False

    def get_tools_for_assistant(self) -> List[ToolDefinition]:
        """
        Get all available MCP tools in univllm format.

        :return: List of ToolDefinitions for use with univllm.
        """
        tools = []
        all_tools = self.manager.get_all_tools()

        for server_name, server_tools in all_tools.items():
            for mcp_tool in server_tools:
                tools.append(mcp_tool_to_univllm_tool(mcp_tool, server_name))

        return tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool call.

        :param tool_name: Full tool name (including server prefix).
        :param arguments: Tool arguments.
        :return: Tool result as a string.
        """
        # Extract server name and original tool name
        if "__" not in tool_name:
            raise ValueError(f"Invalid tool name format: {tool_name}")

        server_name, original_tool_name = tool_name.split("__", 1)

        try:
            result = await self.manager.call_tool(
                server_name, original_tool_name, arguments
            )

            # Format the result as a string
            if hasattr(result, "content"):
                # MCP result format
                content_parts = []
                for item in result.content:
                    if hasattr(item, "text"):
                        content_parts.append(item.text)
                    elif hasattr(item, "type") and item.type == "text":
                        content_parts.append(str(item))
                return "\n".join(content_parts) if content_parts else str(result)
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error executing tool: {e}"

    def __del__(self):
        """Cleanup on deletion."""
        if self._connected:
            # Note: This is not ideal for async cleanup, but serves as a safety net
            logger.warning("MCPToolHandler deleted while still connected")
