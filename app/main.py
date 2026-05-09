
import asyncio
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.health import HealthChecker
from app.infrastructure.sqlite import SQLiteManager
from app.api.deps import init_schema, get_notification_service
from app.api.m1_routes import router as m1_router
from app.api.m2_routes import router as m2_router
from app.api.m4_routes import router as m4_router
from app.api.m5_auth_routes import router as m5_router
from app.api.ui_routes import router as ui_router


# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = SQLiteManager()
health_checker = HealthChecker(db_manager)

# Create FastAPI app
app = FastAPI(
    title="Systeme de reservation de plateaux sportifs",
    debug=settings.DEBUG,
    version="1.0.0"
)

# Include API routers
app.include_router(m1_router)
app.include_router(m2_router)
app.include_router(m4_router)
app.include_router(m5_router)
app.include_router(ui_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/Images", StaticFiles(directory="Images"), name="images")


@app.on_event("startup")
def startup() -> None:
    """Initialize application on startup."""
    logger.info(f"Starting application in {settings.ENVIRONMENT} mode")
    init_schema()
    # Start background task for reminders
    loop = asyncio.get_event_loop()
    loop.create_task(reminder_background_worker())
    logger.info("Application startup complete")


@app.on_event("shutdown")
def shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("Application shutting down")


async def reminder_background_worker() -> None:
    """Background task to process due reminders every 60 seconds."""
    notification_service = get_notification_service()
    while True:
        try:
            notification_service.process_due_reminders()
        except Exception as e:
            logger.error(f"Error processing reminders: {e}")
        await asyncio.sleep(60)


# Kubernetes health check endpoints
@app.get("/health/live")
def liveness_probe() -> dict:
    """Liveness probe for Kubernetes."""
    return health_checker.liveness_probe()


@app.get("/health/ready")
def readiness_probe() -> dict:
    """Readiness probe for Kubernetes."""
    return health_checker.readiness_probe()


@app.get("/health/startup")
def startup_probe() -> dict:
    """Startup probe for Kubernetes."""
    return health_checker.startup_probe()


@app.get("/health")
def health() -> dict[str, str]:
    """Legacy health endpoint for backward compatibility."""
    return {"status": "ok"}
