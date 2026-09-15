import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.incident.models import Incident
from app.incident.schemas import IncidentFilters
from app.incident.tasks import send_downtime_email, send_recovery_email
from app.monitor.models import Monitor, MonitorStatus
from app.shared.pagination import PaginationParams, paginate_query


class IncidentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_incidents(
        self, monitor_id: uuid.UUID, pagination: PaginationParams, filters: IncidentFilters
    ) -> tuple[list[Incident], int]:
        query = select(Incident).where(Incident.monitor_id == monitor_id)

        if filters.resolved is True:
            query = query.where(Incident.resolved_at.is_not(None))
        elif filters.resolved is False:
            query = query.where(Incident.resolved_at.is_(None))

        if filters.started_after is not None:
            query = query.where(Incident.started_at >= filters.started_after)
        if filters.started_before is not None:
            query = query.where(Incident.started_at <= filters.started_before)

        return await paginate_query(query, Incident, self.db, pagination, default_sort="started_at")

    # --- Internal methods, called only by the consumer process ---

    async def open_incident(
        self, monitor_id: uuid.UUID, started_at: datetime, response_time_ms: int | None = None
    ) -> Incident:
        incident = Incident(
            monitor_id=monitor_id, started_at=started_at, response_time_ms=response_time_ms
        )
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)

        send_downtime_email.delay(str(monitor_id))

        return incident

    async def resolve_latest_incident(self, monitor_id: uuid.UUID, resolved_at: datetime) -> None:
        result = await self.db.execute(
            select(Incident)
            .where(Incident.monitor_id == monitor_id, Incident.resolved_at.is_(None))
            .order_by(Incident.started_at.desc())
            .limit(1)
        )
        incident = result.scalar_one_or_none()
        if incident is not None:
            incident.resolved_at = resolved_at
            await self.db.commit()
            send_recovery_email.delay(str(monitor_id))

    async def update_status(
        self, monitor_id: uuid.UUID, status: MonitorStatus, checked_at: datetime
    ) -> None:
        # No owner filter — called only by the trusted internal consumer process
        monitor = await self.db.get(Monitor, monitor_id)
        if monitor is not None:
            monitor.last_status = status
            monitor.last_checked_at = checked_at
            await self.db.commit()
