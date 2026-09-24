from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.core.config import get_settings
from app.incident.routes import router as incident_router
from app.monitor.routes import router as monitor_router

settings = get_settings()

app = FastAPI(title="PulseWatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(monitor_router)
app.include_router(incident_router)
