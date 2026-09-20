import time
from dataclasses import dataclass

import httpx

from worker.config import get_settings


@dataclass
class CheckResult:
    status: str  # "up" | "down"
    response_time_ms: int | None
    checked_at: float


async def check_url(client: httpx.AsyncClient, url: str) -> CheckResult:
    settings = get_settings()
    started = time.monotonic()

    try:
        response = await client.get(url, timeout=settings.http_timeout_seconds)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        status = "up" if response.is_success else "down"
        return CheckResult(status=status, response_time_ms=elapsed_ms, checked_at=time.time())
    except httpx.RequestError:
        # Timeout, connection refused, DNS failure, etc — all treated as down
        return CheckResult(status="down", response_time_ms=None, checked_at=time.time())
