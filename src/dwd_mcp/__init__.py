"""DWD MCP Server - Provides access to German Weather Service data via MCP protocol."""

import asyncio

from .server import main as server_main

__version__ = "0.1.0"


def main() -> None:
    """Entry point for the MCP server."""
    asyncio.run(server_main())
