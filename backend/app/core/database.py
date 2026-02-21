from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
import socket
import re

# Force IPv4 for Render deployment (Render doesn't support IPv6)
# Extract hostname from DATABASE_URL and resolve to IPv4
def get_ipv4_database_url(url: str) -> str:
    """Resolve hostname in DATABASE_URL to IPv4 address to avoid IPv6 issues on Render."""
    # Extract hostname from connection string
    match = re.search(r'@([^:/@]+)', url)
    if match:
        hostname = match.group(1)
        try:
            # Force IPv4 resolution
            ipv4 = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
            # Replace hostname with IPv4 in URL, but keep original host for SSL
            url_with_ip = url.replace(f'@{hostname}', f'@{ipv4}')
            print(f"Resolved {hostname} to IPv4: {ipv4}")
            return url_with_ip
        except Exception as e:
            print(f"Failed to resolve {hostname} to IPv4: {e}, using original URL")
    return url

database_url = get_ipv4_database_url(settings.DATABASE_URL)

# Create database engine
# pool_pre_ping removed — it adds ~400ms per request to remote Supabase.
# pool_recycle handles stale connections; keepalives prevent drops.
engine = create_engine(
    database_url,
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
