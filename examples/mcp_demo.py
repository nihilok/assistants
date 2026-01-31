"""
Example demonstrating MCP (Model Context Protocol) integration.

This example shows how to:
1. Configure MCP servers
2. Enable MCP tools in the UniversalAssistant
3. Use MCP tools in conversations

Prerequisites:
- Install MCP support: pip install "mcp[cli]"
- Configure MCP servers in ~/.config/assistants/mcp.json
"""

import asyncio
from pathlib import Path

from assistants.ai.universal import UniversalAssistant
from assistants.mcp import MCPConfig


async def list_mcp_servers():
    """List all configured MCP servers and their tools."""
    print("=== Configured MCP Servers ===\n")

    # Load MCP configuration
    config = MCPConfig()
    servers = config.list_servers()

    if not servers:
        print("No MCP servers configured.")
        print(
            "Create ~/.config/assistants/mcp.json to configure MCP servers.\n"
        )
        return

    for server_name in servers:
        server = config.get_server(server_name)
        print(f"Server: {server_name}")
        print(f"  Command: {server.command} {' '.join(server.args)}")
        if server.env:
            print(f"  Environment: {server.env}")
        print()


async def demo_mcp_conversation():
    """Demonstrate using an assistant with MCP tools enabled."""
    print("=== MCP-Enabled Assistant Demo ===\n")

    # Create an assistant with MCP tools enabled
    # Note: You need a valid API key for this to work
    assistant = UniversalAssistant(
        model="gpt-4o",
        instructions="You are a helpful assistant with access to external tools.",
        enable_mcp_tools=True,
    )

    print("Assistant created with MCP tools enabled.")
    print(
        "The assistant can now use tools from configured MCP servers.\n"
    )

    # Example conversation (requires valid API key and MCP servers)
    # user_input = "Can you search for information about Python MCP libraries?"
    # response = await assistant.converse(user_input)
    # print(f"Assistant: {response.text_content}")


async def main():
    """Run the MCP examples."""
    print("MCP (Model Context Protocol) Integration Example\n")
    print("=" * 50)
    print()

    # List configured servers
    await list_mcp_servers()

    # Demo conversation with MCP tools
    # Uncomment to test with actual API keys and MCP servers
    # await demo_mcp_conversation()


if __name__ == "__main__":
    asyncio.run(main())
