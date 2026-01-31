"""
MCP server connection and tool management.

This module provides functionality to connect to MCP servers via stdio
and manage their tools for use in AI assistant conversations.
"""

import logging
from contextlib import AbstractAsyncContextManager
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from assistants.mcp.config import MCPConfig, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPServerConnection:
    """Manages a connection to a single MCP server."""

    def __init__(self, config: MCPServerConfig):
        """
        Initialize an MCP server connection.

        :param config: Configuration for the MCP server.
        """
        self.config = config
        self.session: Optional[ClientSession] = None
        self._stdio_transport: Optional[
            AbstractAsyncContextManager[Tuple[Any, Any]]
        ] = None
        self._tools: List[Tool] = []

    async def connect(self) -> None:
        """Connect to the MCP server."""
        try:
            # Set up server parameters
            params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env,
            )

            # Create stdio transport (context manager)
            self._stdio_transport = stdio_client(params)
            read_stream, write_stream = await self._stdio_transport.__aenter__()

            # Create session
            self.session = ClientSession(read_stream, write_stream)
            await self.session.__aenter__()
            await self.session.initialize()

            # Fetch available tools
            await self._fetch_tools()

            logger.info(
                f"Connected to MCP server '{self.config.name}' with {len(self._tools)} tools"
            )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.config.name}': {e}")
            raise

    async def _fetch_tools(self) -> None:
        """Fetch available tools from the server."""
        if not self.session:
            return

        try:
            response = await self.session.list_tools()
            self._tools = response.tools
        except Exception as e:
            logger.error(f"Failed to fetch tools from '{self.config.name}': {e}")
            self._tools = []

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error disconnecting from '{self.config.name}': {e}")
            finally:
                self.session = None
                self._stdio_transport = None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        :param tool_name: Name of the tool to call.
        :param arguments: Arguments for the tool.
        :return: Tool result.
        """
        if not self.session:
            raise RuntimeError(f"Not connected to server '{self.config.name}'")

        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(
                f"Error calling tool '{tool_name}' on '{self.config.name}': {e}"
            )
            raise

    def get_tools(self) -> List[Tool]:
        """Get the list of available tools."""
        return self._tools


class MCPManager:
    """Manages multiple MCP server connections."""

    def __init__(self, config: Optional[MCPConfig] = None):
        """
        Initialize the MCP manager.

        :param config: MCP configuration. If None, will load from default location.
        """
        self.config = config or MCPConfig()
        self.connections: Dict[str, MCPServerConnection] = {}

    async def connect_all(self) -> None:
        """Connect to all configured MCP servers."""
        for server_name in self.config.list_servers():
            await self.connect_server(server_name)

    async def connect_server(self, server_name: str) -> None:
        """
        Connect to a specific MCP server.

        :param server_name: Name of the server to connect to.
        """
        server_config = self.config.get_server(server_name)
        if not server_config:
            logger.warning(f"Server '{server_name}' not found in configuration")
            return

        if server_name in self.connections:
            logger.info(f"Already connected to server '{server_name}'")
            return

        connection = MCPServerConnection(server_config)
        try:
            await connection.connect()
            self.connections[server_name] = connection
        except Exception as e:
            logger.error(f"Failed to connect to server '{server_name}': {e}")

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for connection in self.connections.values():
            await connection.disconnect()
        self.connections.clear()

    async def disconnect_server(self, server_name: str) -> None:
        """
        Disconnect from a specific MCP server.

        :param server_name: Name of the server to disconnect from.
        """
        connection = self.connections.get(server_name)
        if connection:
            await connection.disconnect()
            del self.connections[server_name]

    def get_all_tools(self) -> Dict[str, List[Tool]]:
        """
        Get all available tools from all connected servers.

        :return: Dictionary mapping server names to their tools.
        """
        return {
            server_name: connection.get_tools()
            for server_name, connection in self.connections.items()
        }

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool on a specific server.

        :param server_name: Name of the server.
        :param tool_name: Name of the tool.
        :param arguments: Tool arguments.
        :return: Tool result.
        """
        connection = self.connections.get(server_name)
        if not connection:
            raise ValueError(f"Not connected to server '{server_name}'")

        return await connection.call_tool(tool_name, arguments)

    def list_servers(self) -> List[str]:
        """List all configured servers."""
        return self.config.list_servers()

    def list_connected_servers(self) -> List[str]:
        """List currently connected servers."""
        return list(self.connections.keys())
