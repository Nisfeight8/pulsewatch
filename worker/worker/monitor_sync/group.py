import logging

import redis.asyncio as redis
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)

STREAM_KEY = "monitor_events"
GROUP_NAME = "worker_monitor_sync"
DLQ_KEY = f"{STREAM_KEY}_dlq"


async def ensure_consumer_group(client: redis.Redis) -> None:
    try:
        await client.xgroup_create(name=STREAM_KEY, groupname=GROUP_NAME, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
        logger.debug("Consumer group %s already exists", GROUP_NAME)
