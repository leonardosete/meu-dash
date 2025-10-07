import logging
import sys


def setup_logging():
    """
    Configures the root logger for the application.

    - Logs to stdout, which is standard for containerized applications.
    - Uses a structured format with timestamp, logger name, level, and message.
    - Sets the default logging level to INFO.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
