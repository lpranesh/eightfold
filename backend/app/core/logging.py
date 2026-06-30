"""Logging configuration."""

import logging
import sys


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silence noisy loggers
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
