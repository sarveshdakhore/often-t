import logging
import sys

def setup_logging():
    """Configures basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    # You can add more sophisticated logging handlers here (e.g., file logging)
