"""
Unit tests for the logging configuration utility.
"""

import logging

import pytest

from euvd_mcp.utils.logging_config import configure_logging


@pytest.fixture(autouse=True)
def reset_euvd_logger():
    """Remove all handlers from the euvd_mcp logger after each test."""
    yield
    logger = logging.getLogger("euvd_mcp")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)


class TestConfigureLogging:
    def test_adds_stream_handler(self):
        configure_logging("INFO")
        logger = logging.getLogger("euvd_mcp")
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_sets_correct_level_info(self):
        configure_logging("INFO")
        assert logging.getLogger("euvd_mcp").level == logging.INFO

    def test_sets_correct_level_debug(self):
        configure_logging("DEBUG")
        assert logging.getLogger("euvd_mcp").level == logging.DEBUG

    def test_sets_correct_level_warning(self):
        configure_logging("WARNING")
        assert logging.getLogger("euvd_mcp").level == logging.WARNING

    def test_case_insensitive_level(self):
        configure_logging("debug")
        assert logging.getLogger("euvd_mcp").level == logging.DEBUG

    def test_does_not_add_duplicate_handlers(self):
        configure_logging("INFO")
        configure_logging("INFO")
        assert len(logging.getLogger("euvd_mcp").handlers) == 1

    def test_does_not_propagate(self):
        configure_logging("INFO")
        assert logging.getLogger("euvd_mcp").propagate is False

    def test_child_logger_inherits_handler(self):
        configure_logging("DEBUG")
        child = logging.getLogger("euvd_mcp.controllers.euvd_api")
        # Child has no handlers of its own; effective level is inherited
        assert child.getEffectiveLevel() == logging.DEBUG
