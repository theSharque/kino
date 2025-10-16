import logging
import os
import sys


def setup_logging() -> logging.Logger:
    """Configure root Kino logger once based on LOG_LEVEL.

    Returns the configured logger instance for convenience.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("kino")

    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)

    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a namespaced Kino logger.

    Call setup_logging() early in the app lifecycle to configure handlers.
    """
    full_name = "kino" if not name else f"kino.{name}"
    return logging.getLogger(full_name)


