from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Create database engine
# pool_pre_ping removed — it adds ~400ms per request to remote Supabase.
# pool_recycle handles stale connections; keepalives prevent drops.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=False,
    pool_size=10,
    max_overflow=10,
    pool_recycle=1800,
    pool_timeout=10,
    echo=False,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency to get database session.
    Use with FastAPI Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
