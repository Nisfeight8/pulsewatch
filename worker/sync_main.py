import asyncio
import logging
import os
import signal
import socket

from worker.monitor_sync import EventConsumer
from worker.redis_client import get_redis_client
from worker.state import MonitorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_consumer_name() -> str:
    return os.environ.get("CONSUMER_NAME", f"sync-{socket.gethostname()}-{os.getpid()}")


async def main() -> None:
    client = get_redis_client()
    store = MonitorStore(client)
    await store.load_from_snapshot()

    consumer = EventConsumer(consumer_name=build_consumer_name(), store=store)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, consumer.request_shutdown)

    logger.info("Monitor sync consumer starting")
    await consumer.run(client)

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
