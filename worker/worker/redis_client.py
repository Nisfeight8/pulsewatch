from functools import lru_cache

import redis.asyncio as redis

from worker.config import get_settings


@lru_cache
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=10)
