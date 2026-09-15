import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.monitor.exceptions import MonitorNotFoundError
from app.monitor.models import Monitor
from app.monitor.schemas import MonitorCreate, MonitorUpdate


class MonitorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_monitor(self, owner_id: uuid.UUID, monitor_in: MonitorCreate) -> Monitor:
        monitor = Monitor(
            owner_id=owner_id,
            name=monitor_in.name,
            url=str(monitor_in.url),
            interval_seconds=monitor_in.interval_seconds,
        )
        self.db.add(monitor)
        await self.db.commit()
        await self.db.refresh(monitor)
        return monitor

    async def list_monitors(self, owner_id: uuid.UUID) -> list[Monitor]:
        result = await self.db.execute(select(Monitor).where(Monitor.owner_id == owner_id))
        return list(result.scalars().all())

    async def get_monitor(self, owner_id: uuid.UUID, monitor_id: uuid.UUID) -> Monitor:
        result = await self.db.execute(
            select(Monitor).where(Monitor.id == monitor_id, Monitor.owner_id == owner_id)
        )
        monitor = result.scalar_one_or_none()
        if monitor is None:
            raise MonitorNotFoundError
        return monitor

    async def update_monitor(
        self, owner_id: uuid.UUID, monitor_id: uuid.UUID, monitor_in: MonitorUpdate
    ) -> Monitor:
        monitor = await self.get_monitor(owner_id, monitor_id)

        update_data = monitor_in.model_dump(exclude_unset=True)
        if "url" in update_data:
            update_data["url"] = str(update_data["url"])

        for field, value in update_data.items():
            setattr(monitor, field, value)

        await self.db.commit()
        await self.db.refresh(monitor)
        return monitor

    async def delete_monitor(self, owner_id: uuid.UUID, monitor_id: uuid.UUID) -> None:
        monitor = await self.get_monitor(owner_id, monitor_id)
        await self.db.delete(monitor)
        await self.db.commit()
