from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.monitor.service import MonitorService


def get_monitor_service(db: AsyncSession = Depends(get_db)) -> MonitorService:
    return MonitorService(db)
