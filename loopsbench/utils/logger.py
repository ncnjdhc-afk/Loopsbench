"""Centralized logger for LoopsBench."""

import logging


def setup_logger(name: str) -> logging.Logger:
    """Create and return a logger with the given name."""
    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)
    return _logger


logger = setup_logger("loopsbench")
