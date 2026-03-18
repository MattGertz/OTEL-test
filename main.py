import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    try:
        logger.info("Starting application")
        print("Hello, World!")
        logger.info("Application finished")
    except Exception:
        logger.exception("Unhandled error in main")
        raise


if __name__ == "__main__":
    asyncio.run(main())
