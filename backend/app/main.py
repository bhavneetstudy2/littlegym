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


def _seed_gymnastics_curriculum(engine):
    """Idempotent seed: create Gymnastics Foundation curriculum + skills for all centers with a 'Beasts' batch."""
    from sqlalchemy.orm import Session
    from app.models import Curriculum, ActivityCategory, ProgressionLevel, Batch, BatchMapping

    CURRICULUM_NAME = "Gymnastics Foundation"
    SKILLS = [
        ("Floor Skills", "Log Roll"), ("Floor Skills", "Forward Roll"),
        ("Floor Skills", "Backward Roll"), ("Floor Skills", "Monkey Movement"),
        ("Floor Skills", "Donkey Kick"), ("Floor Skills", "Tummy Roll"),
        ("Beam & Bar - Balance", "Side Walk"), ("Beam & Bar - Balance", "Back Walk"),
        ("Beam & Bar - Balance", "Front Walk"), ("Beam & Bar - Balance", "Kick Walk"),
        ("Beam & Bar - Balance", "Low Beam Walk"), ("Beam & Bar - Balance", "High Beam Walk"),
        ("Beam & Bar - Balance", "Balancing"),
        ("Beam & Bar - Hanging", "Hang Hold"), ("Beam & Bar - Hanging", "Hang & Swing"),
        ("Beam & Bar - Hanging", "Front Support"), ("Beam & Bar - Hanging", "Backseat Circle"),
        ("Beam & Bar - Hanging", "Tommy Roll"),
        ("Vault", "Jump on Springboard"), ("Vault", "Balance on Hot Dog"),
    ]
    LEVELS = [(1, "Not Attempted"), (2, "With Support"), (3, "Without Support")]

    with Session(engine) as db:
        # Find all centers that have a Beasts batch
        beasts_batches = db.query(Batch).filter(
            Batch.name.ilike("%beasts%"), Batch.active == True
        ).all()
        center_ids = list({b.center_id for b in beasts_batches})

        if not center_ids:
            return  # Nothing to seed

        for center_id in center_ids:
            # Get or create curriculum for this center
            curriculum = db.query(Curriculum).filter(
                Curriculum.name == CURRICULUM_NAME,
                Curriculum.center_id == center_id,
            ).first()
            if not curriculum:
                curriculum = Curriculum(
                    name=CURRICULUM_NAME,
                    description="Core gymnastics skills for the Beasts batch",
                    center_id=center_id,
                    is_global=False,
                    active=True,
                    curriculum_type="GYMNASTICS",
                )
                db.add(curriculum)
                db.flush()

            # Create skills
            for order, (group, skill_name) in enumerate(SKILLS):
                cat = db.query(ActivityCategory).filter(
                    ActivityCategory.curriculum_id == curriculum.id,
                    ActivityCategory.name == skill_name,
                ).first()
                if not cat:
                    cat = ActivityCategory(
                        curriculum_id=curriculum.id,
                        name=skill_name,
                        category_group=group,
                        measurement_type="LEVEL",
                        display_order=order,
                        active=True,
                    )
                    db.add(cat)
                    db.flush()

                for level_num, level_name in LEVELS:
                    exists = db.query(ProgressionLevel).filter(
                        ProgressionLevel.activity_category_id == cat.id,
                        ProgressionLevel.level_number == level_num,
                    ).first()
                    if not exists:
                        db.add(ProgressionLevel(
                            activity_category_id=cat.id,
                            level_number=level_num,
                            name=level_name,
                        ))

            # Map all Beasts batches for this center to this curriculum
            center_beasts = [b for b in beasts_batches if b.center_id == center_id]
            for batch in center_beasts:
                mapping = db.query(BatchMapping).filter(
                    BatchMapping.batch_id == batch.id,
                    BatchMapping.center_id == center_id,
                ).first()
                if not mapping:
                    db.add(BatchMapping(
                        batch_id=batch.id,
                        curriculum_id=curriculum.id,
                        center_id=center_id,
                        is_archived=False,
                    ))
                elif mapping.curriculum_id != curriculum.id:
                    mapping.curriculum_id = curriculum.id

        db.commit()


def _seed_trainer_users(engine):
    """Idempotent seed: create trainer accounts for each center + set TRAINER role permissions."""
    from sqlalchemy.orm import Session
    from app.models import User, RolePermission, Center
    from app.utils.enums import UserRole, UserStatus
    from app.core.security import get_password_hash

    # Trainer permissions: view students, attendance, progress only
    TRAINER_PERMISSIONS = [
        "module:students",
        "module:attendance",
        "module:progress",
    ]

    with Session(engine) as db:
        centers = db.query(Center).filter(Center.active == True).all()
        for center in centers:
            # Use center code if available (e.g. CHD), else city name (e.g. mumbai)
            slug = (center.code or center.city or "center").lower().replace(" ", "")
            email = f"trainer.{slug}@thelittlegym.in"

            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                db.add(User(
                    name=f"Trainer {center.name}",
                    email=email,
                    phone="",
                    password_hash=get_password_hash("Trainer@123"),
                    role=UserRole.TRAINER,
                    status=UserStatus.ACTIVE,
                    center_id=center.id,
                ))

            # Set permissions (idempotent)
            for perm_key in TRAINER_PERMISSIONS:
                exists = db.query(RolePermission).filter(
                    RolePermission.center_id == center.id,
                    RolePermission.role == UserRole.TRAINER,
                    RolePermission.permission_key == perm_key,
                ).first()
                if not exists:
                    db.add(RolePermission(
                        center_id=center.id,
                        role=UserRole.TRAINER,
                        permission_key=perm_key,
                        is_allowed=True,
                    ))

        db.commit()


@app.on_event("startup")
async def run_schema_migrations():
    """Run any schema migrations that weren't in initial setup."""
    from app.core.database import engine
    from sqlalchemy import text
    import app.models  # noqa: F401
    from app.models.base import Base

    # Step 1: Add missing columns (always runs, separate try so seeding still runs even if this fails)
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE activity_categories ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE"
            ))
            conn.execute(text(
                "ALTER TABLE curricula ADD COLUMN IF NOT EXISTS curriculum_type VARCHAR(50) NOT NULL DEFAULT 'GYMNASTICS'"
            ))
            conn.commit()
        logger.info("Schema migration: columns ensured")
    except Exception as e:
        logger.warning(f"Schema migration (columns) warning: {e}")

    # Step 2: Create any missing tables
    try:
        Base.metadata.create_all(engine, checkfirst=True)
        logger.info("Schema migration: tables ensured")
    except Exception as e:
        logger.warning(f"Schema migration (tables) warning: {e}")

    # Step 3: Seed data
    try:
        _seed_gymnastics_curriculum(engine)
        logger.info("Seed: Gymnastics Foundation curriculum ensured")
    except Exception as e:
        logger.warning(f"Seed (curriculum) warning: {e}")

    try:
        _seed_trainer_users(engine)
        logger.info("Seed: trainer users ensured")
    except Exception as e:
        logger.warning(f"Seed (trainers) warning: {e}")


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
