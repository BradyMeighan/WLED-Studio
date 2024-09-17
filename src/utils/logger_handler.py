# src/utils/logger_handler.py

import logging

def logger_handler():
    """
    Returns a logging handler with a predefined format.
    """
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    return handler
