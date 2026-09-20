import asyncio
import logging
import time

import httpx
import redis.asyncio as redis

from worker.checker import check_url
from worker.config import get_settings
from worker.state import MonitorSnapshot, MonitorStore
from worker.status_events import publish_status_change

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, store: MonitorStore, redis_client: redis.Redis) -> None:
        self.store = store
        self.redis = redis_client
        self._shutdown = asyncio.Event()
        settings = get_settings()
        self._semaphore = asyncio.Semaphore(settings.check_concurrency)

    def request_shutdown(self, *_args: object) -> None:
        logger.info("Shutdown requested, finishing current tick...")
        self._shutdown.set()

    async def run(self) -> None:
        settings = get_settings()
        async with httpx.AsyncClient() as http_client:
            while not self._shutdown.is_set():
                await self._tick(http_client)
                await asyncio.sleep(settings.tick_interval_seconds)

    async def _tick(self, http_client: httpx.AsyncClient) -> None:
        await self.store.load_from_snapshot()  # re-sync from the Hash the sync process maintains

        due = self.store.due_for_check(now=time.time())
        if not due:
            return

        logger.debug("Checking %d due monitor(s)", len(due))
        await asyncio.gather(*(self._check_one(http_client, m) for m in due))

    async def _check_one(self, http_client: httpx.AsyncClient, monitor: MonitorSnapshot) -> None:
        async with self._semaphore:
            result = await check_url(http_client, monitor.url)

        status_changed = result.status != monitor.last_known_status
        self.store.mark_checked(monitor.id, result.checked_at, result.status)

        if status_changed:
            logger.info(
                "Monitor %s (%s) changed %s -> %s",
                monitor.id,
                monitor.name,
                monitor.last_known_status,
                result.status,
            )
            await publish_status_change(self.redis, monitor.id, result)
