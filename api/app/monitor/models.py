import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import Base, TimestampMixin

if TYPE_CHECKING:
    from app.auth.models import User


class MonitorStatus(enum.StrEnum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


class Monitor(Base, TimestampMixin):
    __tablename__ = "monitors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Denormalized for fast dashboard reads — updated by the checker worker
    last_status: Mapped[MonitorStatus] = mapped_column(
        Enum(MonitorStatus, name="monitor_status"), default=MonitorStatus.UNKNOWN
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    owner: Mapped["User"] = relationship()
    version: Mapped[int] = mapped_column(default=1, server_default="1")
