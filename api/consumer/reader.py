import asyncio
import logging

import redis.asyncio as redis
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.redis import get_redis_client
from consumer.group import GROUP_NAME, STREAM_KEY, ensure_consumer_group
from consumer.handlers import InvalidEventError, handle_status_change

logger = logging.getLogger(__name__)

BLOCK_MS = 5000
BATCH_SIZE = 10
CLAIM_IDLE_MS = 60_000
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
DLQ_SUFFIX = "_dlq"


class ConsumerRunner:
    def __init__(self, consumer_name: str) -> None:
        self.consumer_name = consumer_name
        self.dlq_key = f"{STREAM_KEY}{DLQ_SUFFIX}"
        self._shutdown = asyncio.Event()

    def request_shutdown(self, *_args: object) -> None:
        logger.info("Shutdown requested, finishing in-flight batch...")
        self._shutdown.set()

    async def run(self) -> None:
        client = get_redis_client()
        await ensure_consumer_group(client)
        logger.info("Consumer %s listening on %s", self.consumer_name, STREAM_KEY)

        while not self._shutdown.is_set():
            await self._reclaim_stale(client)
            await self._process_batch(client)

        await client.aclose()

    async def _process_batch(self, client: redis.Redis) -> None:
        try:
            response = await client.xreadgroup(
                groupname=GROUP_NAME,
                consumername=self.consumer_name,
                streams={STREAM_KEY: ">"},
                count=BATCH_SIZE,
                block=BLOCK_MS,
            )
        except RedisTimeoutError:
            return

        if not response:
            return

        for _stream_key, messages in response:
            for message_id, fields in messages:
                await self._handle_message(client, message_id, fields)

    async def _reclaim_stale(self, client: redis.Redis) -> None:
        _cursor, claimed, _deleted = await client.xautoclaim(
            name=STREAM_KEY,
            groupname=GROUP_NAME,
            consumername=self.consumer_name,
            min_idle_time=CLAIM_IDLE_MS,
            start_id="0-0",
            count=BATCH_SIZE,
        )
        for message_id, fields in claimed:
            await self._handle_message(client, message_id, fields)

    async def _handle_message(
        self, client: redis.Redis, message_id: str, fields: dict[str, str]
    ) -> None:
        last_error: str | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await handle_status_change(fields)
            except InvalidEventError as exc:
                # Malformed data — retrying will never fix this, straight to DLQ
                logger.warning("Malformed event %s: %s", message_id, exc)
                await self._send_to_dlq(client, message_id, fields, str(exc))
                await self._ack(client, message_id)
                return
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Error processing %s (attempt %d/%d): %s",
                    message_id,
                    attempt,
                    MAX_RETRIES,
                    last_error,
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
            else:
                await self._ack(client, message_id)
                return

        logger.error("Max retries exceeded for %s — sending to DLQ", message_id)
        await self._send_to_dlq(client, message_id, fields, last_error or "unknown error")
        await self._ack(client, message_id)

    async def _send_to_dlq(
        self, client: redis.Redis, message_id: str, fields: dict[str, str], error: str
    ) -> None:
        try:
            await client.xadd(
                self.dlq_key,
                {"original_message_id": message_id, "error": error, **fields},
            )
        except Exception:
            # DLQ itself is down — last resort so we don't loop forever on a
            # poison message. The event is lost; this is logged as critical
            # so it's visible for manual follow-up.
            logger.critical(
                "Failed to write %s to DLQ — acking anyway to avoid poison loop", message_id
            )

    async def _ack(self, client: redis.Redis, message_id: str) -> None:
        try:
            await client.xack(STREAM_KEY, GROUP_NAME, message_id)
        except Exception:
            logger.critical("Failed to ack %s — manual intervention required", message_id)
