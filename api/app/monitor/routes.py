import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.deps import get_current_user
from app.auth.models import User
from app.monitor.deps import get_monitor_service
from app.monitor.exceptions import MonitorNotFoundError
from app.monitor.models import Monitor
from app.monitor.schemas import MonitorCreate, MonitorRead, MonitorUpdate
from app.monitor.service import MonitorService

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    monitor_in: MonitorCreate,
    current_user: User = Depends(get_current_user),
    monitor_service: MonitorService = Depends(get_monitor_service),
) -> Monitor:
    return await monitor_service.create_monitor(current_user.id, monitor_in)


@router.get("", response_model=list[MonitorRead])
async def list_monitors(
    current_user: User = Depends(get_current_user),
    monitor_service: MonitorService = Depends(get_monitor_service),
) -> list[Monitor]:
    return await monitor_service.list_monitors(current_user.id)


@router.get("/{monitor_id}", response_model=MonitorRead)
async def get_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    monitor_service: MonitorService = Depends(get_monitor_service),
) -> Monitor:
    try:
        return await monitor_service.get_monitor(current_user.id, monitor_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found"
        ) from None


@router.patch("/{monitor_id}", response_model=MonitorRead)
async def update_monitor(
    monitor_id: uuid.UUID,
    monitor_in: MonitorUpdate,
    current_user: User = Depends(get_current_user),
    monitor_service: MonitorService = Depends(get_monitor_service),
) -> Monitor:
    try:
        return await monitor_service.update_monitor(current_user.id, monitor_id, monitor_in)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found"
        ) from None


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    monitor_service: MonitorService = Depends(get_monitor_service),
) -> None:
    try:
        await monitor_service.delete_monitor(current_user.id, monitor_id)
    except MonitorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found"
        ) from None
