"""
MCP (Model Context Protocol) integration for the assistants framework.

This module provides functionality to connect to MCP servers and use their tools
in conversations with AI assistants.
"""

from assistants.mcp.config import MCPConfig, MCPServerConfig
from assistants.mcp.manager import MCPManager

__all__ = ["MCPConfig", "MCPServerConfig", "MCPManager"]
