from functools import lru_cache
from typing import TYPE_CHECKING

import redis.asyncio as redis

from app.core.config import get_settings

if TYPE_CHECKING:
    from app.monitor.models import Monitor

MONITOR_EVENTS_STREAM = "monitor_events"


@lru_cache
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=10,  # must exceed the longest `block=` used by XREADGROUP
    )


async def publish_monitor_event(client: redis.Redis, action: str, monitor: "Monitor") -> None:
    # Contract with the checker worker — keep both sides in sync if this changes.
    await client.xadd(
        MONITOR_EVENTS_STREAM,
        {
            "action": action,  # "created" | "updated" | "deleted"
            "monitor_id": str(monitor.id),
            "version": str(monitor.version),
            "url": monitor.url,
            "name": monitor.name,
            "interval_seconds": str(monitor.interval_seconds),
            "is_active": str(monitor.is_active),
        },
    )
