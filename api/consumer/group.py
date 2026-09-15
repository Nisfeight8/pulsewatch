import logging

import redis.asyncio as redis
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)

STREAM_KEY = "status_changes"
GROUP_NAME = "incident_consumers"


async def ensure_consumer_group(client: redis.Redis) -> None:
    """Create the consumer group if it doesn't exist yet.

    mkstream=True also creates the stream itself if this is the very
    first consumer process to ever start up.
    """
    try:
        await client.xgroup_create(name=STREAM_KEY, groupname=GROUP_NAME, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
        logger.debug("Consumer group %s already exists", GROUP_NAME)
