import logging
import uuid
from datetime import datetime

from app.core.db import async_session
from app.incident.service import IncidentService
from app.monitor.models import MonitorStatus
from app.monitor.service import MonitorService

logger = logging.getLogger(__name__)


class InvalidEventError(Exception):
    pass


def parse_event(fields: dict[str, str]) -> dict:
    # This shape is the contract with the checker worker — keep both
    # sides in sync if it ever changes.
    try:
        monitor_id = uuid.UUID(fields["monitor_id"])
        status = MonitorStatus(fields["status"])
        checked_at = datetime.fromisoformat(fields["checked_at"])
    except (KeyError, ValueError) as exc:
        raise InvalidEventError(f"malformed event: {exc}") from exc

    raw_response_time = fields.get("response_time_ms")
    response_time_ms = int(raw_response_time) if raw_response_time else None

    return {
        "monitor_id": monitor_id,
        "status": status,
        "checked_at": checked_at,
        "response_time_ms": response_time_ms,
    }


async def handle_status_change(fields: dict[str, str]) -> None:
    event = parse_event(fields)

    async with async_session() as db:
        monitor_service = MonitorService(db)
        incident_service = IncidentService(db)

        await monitor_service.update_status(
            event["monitor_id"], event["status"], event["checked_at"]
        )

        if event["status"] == MonitorStatus.DOWN:
            await incident_service.open_incident(
                event["monitor_id"], event["checked_at"], event["response_time_ms"]
            )
        else:
            await incident_service.resolve_latest_incident(event["monitor_id"], event["checked_at"])
