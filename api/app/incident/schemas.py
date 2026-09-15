import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monitor_id: uuid.UUID
    started_at: datetime
    resolved_at: datetime | None
    response_time_ms: int | None


class IncidentFilters(BaseModel):
    resolved: bool | None = None
    started_after: datetime | None = None
    started_before: datetime | None = None
