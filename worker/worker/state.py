import json
import logging
from dataclasses import asdict, dataclass

import redis.asyncio as redis

logger = logging.getLogger(__name__)

SNAPSHOT_KEY = "monitor_snapshots"


class StaleEventError(Exception):
    """Raised when an incoming event's version is not newer than what we have."""


@dataclass
class MonitorSnapshot:
    id: str
    version: int
    url: str
    name: str
    interval_seconds: int
    is_active: bool
    last_checked_at: float | None = None
    last_known_status: str = "unknown"


class MonitorStore:
    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client
        self._monitors: dict[str, MonitorSnapshot] = {}

    async def load_from_snapshot(self) -> None:
        raw = await self.redis.hgetall(SNAPSHOT_KEY)
        fresh: dict[str, MonitorSnapshot] = {}

        for monitor_id, blob in raw.items():
            data = json.loads(blob)
            snapshot = MonitorSnapshot(**data)

            # Carry over this process's own local tracking state, if it already had this monitor
            existing = self._monitors.get(monitor_id)
            if existing is not None:
                snapshot.last_checked_at = existing.last_checked_at
                snapshot.last_known_status = existing.last_known_status

            fresh[monitor_id] = snapshot

        self._monitors = fresh
        logger.info("Synced %d monitor snapshots from Redis", len(fresh))

    async def upsert(self, snapshot: MonitorSnapshot) -> None:
        existing = self._monitors.get(snapshot.id)

        if existing is not None:
            if snapshot.version <= existing.version:
                raise StaleEventError(
                    f"monitor {snapshot.id}: incoming v{snapshot.version} <= stored v{existing.version}"
                )
            # Local-only tracking fields aren't in the API's event — carry them over
            snapshot.last_checked_at = existing.last_checked_at
            snapshot.last_known_status = existing.last_known_status

        self._monitors[snapshot.id] = snapshot
        await self.redis.hset(SNAPSHOT_KEY, snapshot.id, json.dumps(asdict(snapshot)))

    async def remove(self, monitor_id: str, incoming_version: int) -> None:
        existing = self._monitors.get(monitor_id)
        if existing is not None and incoming_version <= existing.version:
            raise StaleEventError(f"monitor {monitor_id}: stale delete v{incoming_version}")

        self._monitors.pop(monitor_id, None)
        await self.redis.hdel(SNAPSHOT_KEY, monitor_id)

    def due_for_check(self, now: float) -> list[MonitorSnapshot]:
        return [
            m
            for m in self._monitors.values()
            if m.is_active
            and (m.last_checked_at is None or now - m.last_checked_at >= m.interval_seconds)
        ]

    def mark_checked(self, monitor_id: str, checked_at: float, status: str) -> None:
        # In-memory only — not re-persisted to the Hash on every tick,
        # only structural changes (upsert/remove) sync back to Redis.
        monitor = self._monitors.get(monitor_id)
        if monitor is not None:
            monitor.last_checked_at = checked_at
            monitor.last_known_status = status
