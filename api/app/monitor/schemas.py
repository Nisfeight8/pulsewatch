import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.monitor.models import MonitorStatus


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    interval_seconds: int = Field(default=60, ge=30)


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    interval_seconds: int | None = Field(default=None, ge=30)
    is_active: bool | None = None


class MonitorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    interval_seconds: int
    is_active: bool
    last_status: MonitorStatus
    last_checked_at: datetime | None
    created_at: datetime


class MonitorFilters(BaseModel):
    is_active: bool | None = None
    status: MonitorStatus | None = None
    search: str | None = None