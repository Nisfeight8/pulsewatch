import asyncio
import logging
import signal

from worker.redis_client import get_redis_client
from worker.scheduler import Scheduler
from worker.state import MonitorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    client = get_redis_client()
    store = MonitorStore(client)
    await store.load_from_snapshot()

    scheduler = Scheduler(store=store, redis_client=client)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, scheduler.request_shutdown)

    logger.info("Scheduler starting")
    await scheduler.run()

    await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
