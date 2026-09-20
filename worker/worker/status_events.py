import redis.asyncio as redis

from worker.checker import CheckResult

STATUS_CHANGES_STREAM = "status_changes"


async def publish_status_change(client: redis.Redis, monitor_id: str, result: CheckResult) -> None:
    # Contract with the API's consumer — keep both sides in sync if this changes.
    fields = {
        "monitor_id": monitor_id,
        "status": result.status,
        "checked_at": _to_iso(result.checked_at),
    }
    if result.response_time_ms is not None:
        fields["response_time_ms"] = str(result.response_time_ms)

    await client.xadd(STATUS_CHANGES_STREAM, fields)


def _to_iso(epoch_seconds: float) -> str:
    from datetime import UTC, datetime

    return datetime.fromtimestamp(epoch_seconds, tz=UTC).isoformat()
