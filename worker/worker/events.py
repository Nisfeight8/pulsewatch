import asyncio
import logging

import redis.asyncio as redis
from redis.exceptions import ResponseError
from redis.exceptions import TimeoutError as RedisTimeoutError

from worker.state import MonitorSnapshot, MonitorStore, StaleEventError

logger = logging.getLogger(__name__)

STREAM_KEY = "monitor_events"
GROUP_NAME = "worker_monitor_sync"
DLQ_KEY = f"{STREAM_KEY}_dlq"

BLOCK_MS = 5000
BATCH_SIZE = 20
CLAIM_IDLE_MS = 60_000
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


class InvalidEventError(Exception):
    pass


def parse_event(fields: dict[str, str]) -> dict:
    try:
        return {
            "action": fields["action"],
            "monitor_id": fields["monitor_id"],
            "version": int(fields["version"]),
            "url": fields.get("url", ""),
            "name": fields.get("name", ""),
            "interval_seconds": int(fields.get("interval_seconds", 60)),
            "is_active": fields.get("is_active") == "True",
        }
    except (KeyError, ValueError) as exc:
        raise InvalidEventError(f"malformed monitor event: {exc}") from exc


async def apply_event(store: MonitorStore, fields: dict[str, str]) -> None:
    event = parse_event(fields)

    if event["action"] in ("created", "updated"):
        snapshot = MonitorSnapshot(
            id=event["monitor_id"],
            version=event["version"],
            url=event["url"],
            name=event["name"],
            interval_seconds=event["interval_seconds"],
            is_active=event["is_active"],
        )
        await store.upsert(snapshot)
    elif event["action"] == "deleted":
        await store.remove(event["monitor_id"], event["version"])
    else:
        raise InvalidEventError(f"unknown action: {event['action']}")


async def ensure_consumer_group(client: redis.Redis) -> None:
    try:
        await client.xgroup_create(name=STREAM_KEY, groupname=GROUP_NAME, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
        logger.debug("Consumer group %s already exists", GROUP_NAME)


class EventConsumer:
    def __init__(self, consumer_name: str, store: MonitorStore) -> None:
        self.consumer_name = consumer_name
        self.store = store
        self._shutdown = asyncio.Event()

    def request_shutdown(self, *_args: object) -> None:
        logger.info("Shutdown requested, finishing in-flight batch...")
        self._shutdown.set()

    async def run(self, client: redis.Redis) -> None:
        await ensure_consumer_group(client)
        logger.info("Event consumer %s listening on %s", self.consumer_name, STREAM_KEY)

        while not self._shutdown.is_set():
            await self._reclaim_stale(client)
            await self._process_batch(client)

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
                await apply_event(self.store, fields)
            except StaleEventError as exc:
                # Not a failure — an out-of-order or replayed event we've
                # already superseded. Ack and move on.
                logger.info("Ignoring stale event %s: %s", message_id, exc)
                await self._ack(client, message_id)
                return
            except InvalidEventError as exc:
                logger.warning("Malformed event %s: %s", message_id, exc)
                await self._send_to_dlq(client, message_id, fields, str(exc))
                await self._ack(client, message_id)
                return
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Error applying event %s (attempt %d/%d): %s",
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
                DLQ_KEY, {"original_message_id": message_id, "error": error, **fields}
            )
        except Exception:
            logger.critical(
                "Failed to write %s to DLQ — acking anyway to avoid poison loop", message_id
            )

    async def _ack(self, client: redis.Redis, message_id: str) -> None:
        try:
            await client.xack(STREAM_KEY, GROUP_NAME, message_id)
        except Exception:
            logger.critical("Failed to ack %s — manual intervention required", message_id)
