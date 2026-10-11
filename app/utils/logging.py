import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures structured format logging to stdout."""
    logger = logging.getLogger("multi_source_rag")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
