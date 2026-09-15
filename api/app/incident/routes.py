import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import get_current_user
from app.auth.models import User
from app.incident.deps import get_incident_service
from app.incident.models import Incident
from app.incident.schemas import IncidentRead
from app.incident.service import IncidentService
from app.monitor.deps import get_monitor_service
from app.monitor.exceptions import MonitorNotFoundError
from app.monitor.service import MonitorService

router = APIRouter(prefix="/monitors/{monitor_id}/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    monitor_service: MonitorService = Depends(get_monitor_service),
    incident_service: IncidentService = Depends(get_incident_service),
) -> list[Incident]:
    try:
        # Ownership check happens here — 404 if the monitor isn't the caller's
        await monitor_service.get_monitor(current_user.id, monitor_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found"
        ) from None

    return await incident_service.list_incidents(monitor_id)
