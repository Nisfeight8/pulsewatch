import asyncio
import uuid

from app.auth.models import User
from app.core.celery_app import celery_app
from app.core.db import async_session
from app.core.email import send_email
from app.monitor.models import Monitor


@celery_app.task(name="incident.send_downtime_email")
def send_downtime_email(monitor_id: str) -> None:
    # Celery tasks are sync — bridge into our async DB/email code here
    asyncio.run(_send_downtime_email(uuid.UUID(monitor_id)))


async def _send_downtime_email(monitor_id: uuid.UUID) -> None:
    async with async_session() as db:
        monitor = await db.get(Monitor, monitor_id)
        if monitor is None:
            return

        owner = await db.get(User, monitor.owner_id)
        if owner is None:
            return

        await send_email(
            to=owner.email,
            subject=f"[PulseWatch] {monitor.name} is down",
            html_body=(
                f"<p>Your monitor <strong>{monitor.name}</strong> "
                f"({monitor.url}) appears to be down.</p>"
            ),
        )


@celery_app.task(name="incident.send_recovery_email")
def send_recovery_email(monitor_id: str) -> None:
    asyncio.run(_send_recovery_email(uuid.UUID(monitor_id)))


async def _send_recovery_email(monitor_id: uuid.UUID) -> None:
    async with async_session() as db:
        monitor = await db.get(Monitor, monitor_id)
        if monitor is None:
            return

        owner = await db.get(User, monitor.owner_id)
        if owner is None:
            return

        await send_email(
            to=owner.email,
            subject=f"[PulseWatch] {monitor.name} is back up",
            html_body=(
                f"<p>Good news — your monitor <strong>{monitor.name}</strong> "
                f"({monitor.url}) is responding again.</p>"
            ),
        )
