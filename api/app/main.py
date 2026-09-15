from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.incident.routes import router as incident_router
from app.monitor.routes import router as monitor_router

app = FastAPI(title="PulseWatch API")

app.include_router(auth_router)
app.include_router(monitor_router)
app.include_router(incident_router)
