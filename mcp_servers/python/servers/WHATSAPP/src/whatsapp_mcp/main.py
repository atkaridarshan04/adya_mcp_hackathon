#!/usr/bin/env python3
"""Entry point for WhatsApp MCP Server."""

import asyncio
import logging
import sys

import click

from whatsapp_mcp.server import main as server_main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


@click.command()
@click.version_option()
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging")
def main(debug: bool) -> None:
    """WhatsApp MCP Server - A server that provides a Model Context Protocol interface to interact with WhatsApp Business API."""
    # Set logging level
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run the server
    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
