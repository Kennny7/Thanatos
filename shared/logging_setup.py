# shared\logging_setup.py
import os
import logging.config

from config.settings import app_config


def setup_logging():
    log_dir = app_config.log_dir
    os.makedirs(log_dir, exist_ok=True)

    logging.config.fileConfig(
        app_config.log_config_path,
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