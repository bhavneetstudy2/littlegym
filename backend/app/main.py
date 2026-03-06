import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Multi-tenant CRM for The Little Gym centers"
)

# CORS middleware - origins from settings (configurable via ALLOWED_ORIGINS env var)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
    "https://littlegym-frontend.onrender.com",
]
logger.info(f"🔐 Configuring CORS with origins: {CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routers
from app.api.v1 import auth, centers, leads, intro_visits, enrollments, attendance, curriculum, report_cards, csv_import, weekly_progress, settings
from app.api.v1.mdm import class_types

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(centers.router, prefix="/api/v1")
app.include_router(leads.router, prefix="/api/v1")
app.include_router(intro_visits.router, prefix="/api/v1")
app.include_router(enrollments.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(curriculum.router, prefix="/api/v1")
app.include_router(class_types.router, prefix="/api/v1")
app.include_router(report_cards.router, prefix="/api/v1")
app.include_router(csv_import.router, prefix="/api/v1")
app.include_router(weekly_progress.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")


@app.on_event("startup")
async def run_schema_migrations():
    """Run any schema migrations that weren't in initial setup."""
    try:
        from app.core.database import engine
        from sqlalchemy import text
        # Import all models so their metadata is registered before create_all
        import app.models  # noqa: F401
        from app.models.base import Base

        # Create any missing tables (no-op for existing tables)
        Base.metadata.create_all(engine, checkfirst=True)
        logger.info("Schema migration: ensured all tables exist")

        # Add activity_categories.active column if it was created before this column existed
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE activity_categories ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE"
            ))
            conn.commit()
        logger.info("Schema migration: activity_categories.active column ensured")
    except Exception as e:
        logger.warning(f"Schema migration warning (non-fatal): {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": settings.APP_NAME, "version": settings.VERSION}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
