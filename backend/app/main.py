from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Multi-tenant CRM for The Little Gym centers"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Include routers after they are created
# from app.api.v1 import auth, centers, users, leads
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(centers.router, prefix="/api/v1/centers", tags=["centers"])


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": settings.APP_NAME, "version": settings.VERSION}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
