"""
MCP configuration file handling.

This module provides functionality to read and parse MCP server configurations
from JSON files.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from assistants.config.file_management import CONFIG_DIR


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "MCPServerConfig":
        """Create an MCPServerConfig from a dictionary."""
        return cls(
            name=name,
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env"),
        )


class MCPConfig:
    """Manager for MCP configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize MCP configuration.

        :param config_path: Path to the MCP config file. Defaults to
                           ~/.config/assistants/mcp.json
        """
        self.config_path = config_path or CONFIG_DIR / "mcp.json"
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load MCP server configurations from the JSON file."""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            mcp_servers = data.get("mcpServers", {})
            for name, server_data in mcp_servers.items():
                self.servers[name] = MCPServerConfig.from_dict(name, server_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in MCP configuration file: {e}") from e
        except KeyError as e:
            raise ValueError(f"Missing required field in MCP configuration: {e}") from e
        except TypeError as e:
            raise ValueError(f"Invalid data type in MCP configuration: {e}") from e

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a server configuration by name."""
        return self.servers.get(name)

    def list_servers(self) -> List[str]:
        """List all configured server names."""
        return list(self.servers.keys())
