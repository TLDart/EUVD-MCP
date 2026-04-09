"""
Logging configuration for the EUVD MCP server.

Call configure_logging() once at application startup. All modules under the
euvd_mcp namespace inherit this configuration via the standard logging hierarchy.
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """
    Configure application-wide logging for the euvd_mcp namespace.

    Installs a single StreamHandler on the root euvd_mcp logger. All child
    loggers (euvd_mcp.main, euvd_mcp.controllers.euvd_api, etc.) inherit it
    automatically. Safe to call multiple times — duplicate handlers are avoided.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR). Case-insensitive.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger("euvd_mcp")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers when called more than once (e.g. in tests)
    if logger.handlers:
        return

    # Always log to stderr — stdout is reserved for the MCP stdio transport.
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    logger.addHandler(handler)
    logger.propagate = False
