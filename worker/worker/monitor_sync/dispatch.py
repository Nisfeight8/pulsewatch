from worker.monitor_sync.parser import InvalidEventError, parse_event
from worker.state import MonitorSnapshot, MonitorStore


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
