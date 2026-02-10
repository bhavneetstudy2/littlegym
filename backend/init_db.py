"""Initialize the database tables."""
from app.core.database import engine
from app.models import Base

print("Creating tables in Supabase...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
