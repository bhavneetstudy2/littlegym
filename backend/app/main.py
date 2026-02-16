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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routers
from app.api.v1 import auth, centers, leads, intro_visits, enrollments, attendance, curriculum, report_cards, csv_import, weekly_progress
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
