from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.incident.service import IncidentService


def get_incident_service(db: AsyncSession = Depends(get_db)) -> IncidentService:
    return IncidentService(db)
