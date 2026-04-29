# shared\logging_setup.py
import os
import logging.config

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logging.config.fileConfig(
        "config/logging.conf",
        disable_existing_loggers=False
    )

def ensure_logging():
    """
    Ensures logging is configured.
    Safe to call multiple times.
    """
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        setup_logging()

"""
For testing

from shared.logging_setup import ensure_logging
ensure_logging()

"""