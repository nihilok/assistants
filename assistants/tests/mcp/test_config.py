"""Tests for MCP configuration."""

import json
import tempfile
from pathlib import Path

import pytest

from assistants.mcp.config import MCPConfig, MCPServerConfig


def test_mcp_server_config_from_dict():
    """Test creating MCPServerConfig from a dictionary."""
    data = {
        "command": "python",
        "args": ["server.py", "--port", "8080"],
        "env": {"API_KEY": "secret"},
    }
    config = MCPServerConfig.from_dict("test_server", data)

    assert config.name == "test_server"
    assert config.command == "python"
    assert config.args == ["server.py", "--port", "8080"]
    assert config.env == {"API_KEY": "secret"}


def test_mcp_server_config_from_dict_no_env():
    """Test creating MCPServerConfig without env."""
    data = {"command": "node", "args": ["index.js"]}
    config = MCPServerConfig.from_dict("node_server", data)

    assert config.name == "node_server"
    assert config.command == "node"
    assert config.args == ["index.js"]
    assert config.env is None


def test_mcp_config_load_valid():
    """Test loading valid MCP configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "mcp.json"
        config_data = {
            "mcpServers": {
                "server1": {"command": "python", "args": ["server1.py"]},
                "server2": {
                    "command": "node",
                    "args": ["server2.js"],
                    "env": {"DEBUG": "true"},
                },
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        mcp_config = MCPConfig(config_path)

        assert len(mcp_config.servers) == 2
        assert "server1" in mcp_config.servers
        assert "server2" in mcp_config.servers

        server1 = mcp_config.get_server("server1")
        assert server1 is not None
        assert server1.command == "python"
        assert server1.args == ["server1.py"]

        server2 = mcp_config.get_server("server2")
        assert server2 is not None
        assert server2.env == {"DEBUG": "true"}


def test_mcp_config_load_empty():
    """Test loading empty MCP configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "mcp.json"
        config_data = {"mcpServers": {}}

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        mcp_config = MCPConfig(config_path)

        assert len(mcp_config.servers) == 0
        assert mcp_config.list_servers() == []


def test_mcp_config_nonexistent_file():
    """Test loading when config file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.json"
        mcp_config = MCPConfig(config_path)

        assert len(mcp_config.servers) == 0
        assert mcp_config.get_server("test") is None


def test_mcp_config_invalid_json():
    """Test loading invalid JSON configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "mcp.json"

        with open(config_path, "w", encoding="utf-8") as f:
            f.write("invalid json")

        with pytest.raises(ValueError, match="Invalid JSON in MCP configuration file"):
            MCPConfig(config_path)


def test_mcp_config_missing_command():
    """Test loading configuration with missing required field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "mcp.json"
        config_data = {
            "mcpServers": {
                "server1": {"args": []},  # Missing 'command' field
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with pytest.raises(ValueError, match="Missing required field"):
            MCPConfig(config_path)


def test_mcp_config_list_servers():
    """Test listing configured servers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "mcp.json"
        config_data = {
            "mcpServers": {
                "server1": {"command": "python", "args": []},
                "server2": {"command": "node", "args": []},
                "server3": {"command": "go", "args": []},
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        mcp_config = MCPConfig(config_path)

        servers = mcp_config.list_servers()
        assert len(servers) == 3
        assert "server1" in servers
        assert "server2" in servers
        assert "server3" in servers
