"""
Manually run the MDM migration
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine
from sqlalchemy import text


def run_migration():
    """Run the MDM enhancement migration"""
    db = SessionLocal()

    try:
        print("[INFO] Running MDM enhancements migration...")

        # Add columns to centers table
        print("[1/7] Adding columns to centers table...")
        db.execute(text("ALTER TABLE centers ADD COLUMN code VARCHAR(20)"))
        db.execute(text("ALTER TABLE centers ADD COLUMN state VARCHAR(100)"))
        db.execute(text("ALTER TABLE centers ADD COLUMN email VARCHAR(100)"))
        db.execute(text("ALTER TABLE centers ADD COLUMN active BOOLEAN DEFAULT 1 NOT NULL"))
        db.commit()
        print("  [OK] Centers table updated")

        # Add columns to curricula table
        print("[2/7] Adding columns to curricula table...")
        db.execute(text("ALTER TABLE curricula ADD COLUMN level VARCHAR(50)"))
        db.execute(text("ALTER TABLE curricula ADD COLUMN age_min INTEGER"))
        db.execute(text("ALTER TABLE curricula ADD COLUMN age_max INTEGER"))
        db.commit()
        print("  [OK] Curricula table updated")

        # Create class_types table
        print("[3/7] Creating class_types table...")
        db.execute(text("""
            CREATE TABLE class_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                age_min INTEGER NOT NULL,
                age_max INTEGER NOT NULL,
                duration_minutes INTEGER DEFAULT 45 NOT NULL,
                active BOOLEAN DEFAULT 1 NOT NULL,
                created_by_id INTEGER,
                updated_by_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                is_archived BOOLEAN DEFAULT 0 NOT NULL
            )
        """))
        db.commit()
        print("  [OK] Class_types table created")

        # Create batch_mappings table
        print("[4/7] Creating batch_mappings table...")
        db.execute(text("""
            CREATE TABLE batch_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                class_type_id INTEGER,
                curriculum_id INTEGER,
                center_id INTEGER NOT NULL,
                created_by_id INTEGER,
                updated_by_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                is_archived BOOLEAN DEFAULT 0 NOT NULL,
                FOREIGN KEY (batch_id) REFERENCES batches(id),
                FOREIGN KEY (class_type_id) REFERENCES class_types(id),
                FOREIGN KEY (curriculum_id) REFERENCES curricula(id),
                FOREIGN KEY (center_id) REFERENCES centers(id)
            )
        """))
        db.commit()
        print("  [OK] Batch_mappings table created")

        # Create indexes
        print("[5/7] Creating indexes...")
        db.execute(text("CREATE INDEX ix_centers_code ON centers(code)"))
        db.execute(text("CREATE INDEX ix_centers_active ON centers(active)"))
        db.execute(text("CREATE INDEX ix_class_types_name ON class_types(name)"))
        db.execute(text("CREATE INDEX ix_class_types_active ON class_types(active)"))
        db.execute(text("CREATE INDEX ix_batch_mappings_batch_id ON batch_mappings(batch_id)"))
        db.execute(text("CREATE INDEX ix_batch_mappings_center_id ON batch_mappings(center_id)"))
        db.execute(text("CREATE INDEX ix_curricula_name ON curricula(name)"))
        db.execute(text("CREATE INDEX ix_curricula_active ON curricula(active)"))
        db.commit()
        print("  [OK] Indexes created")

        # Update existing center to be active
        print("[6/7] Updating existing center...")
        db.execute(text("UPDATE centers SET active = 1 WHERE active IS NULL"))
        db.commit()
        print("  [OK] Existing center updated")

        print("\n[SUCCESS] Migration completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        db.rollback()
        return False
    finally:
        db.close()

    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
