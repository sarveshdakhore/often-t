import asyncio
import logging
import sys # Import sys
from .load_demo_data import main as run_seed

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Running seed script via python -m seed...")
    # Ensure event loop policy is set for Windows if needed
    # if sys.platform == "win32":
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_seed())
