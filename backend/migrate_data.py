"""Migrate data from Supabase to Render PostgreSQL."""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Source: Supabase
SOURCE_DB = "postgresql+psycopg://postgres:cBS3OJZ0qMBNTV2c@db.ycmxswxwwpsbrqyycsyb.supabase.co:5432/postgres"

# Target: Render
TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"

source_engine = create_engine(SOURCE_DB)
target_engine = create_engine(TARGET_DB)

SourceSession = sessionmaker(bind=source_engine)
TargetSession = sessionmaker(bind=target_engine)

source_db = SourceSession()
target_db = TargetSession()

print("Starting data migration from Supabase to Render...")

# Get list of tables to migrate (in order to handle foreign keys)
tables_order = [
    'centers',
    'users',
    'parents',
    'children',
    'family_links',
    'enquiries',
    'intro_visits',
    'leads',
    'lead_activities',
    'batches',
    'class_sessions',
    'enrollments',
    'payments',
    'discounts',
    'attendance',
    'curricula',
    'skills',
    'skill_progress',
    'report_cards',
    'class_types',
    'age_groups',
    'activity_categories',
    'progression_levels',
    'weekly_progress',
    'child_trainer_notes'
]

# Clear existing data in target (except alembic_version)
print("\nClearing existing data in target database...")
for table in reversed(tables_order):
    try:
        target_db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        print(f"  Cleared {table}")
    except Exception as e:
        print(f"  Skipped {table}: {str(e)[:50]}")
target_db.commit()

# Migrate data table by table
print("\nMigrating data...")
for table in tables_order:
    try:
        # Get data from source
        source_data = source_db.execute(text(f"SELECT * FROM {table}")).fetchall()

        if not source_data:
            print(f"  {table}: No data to migrate")
            continue

        # Get column names
        columns = source_data[0]._fields

        # Insert into target
        for row in source_data:
            placeholders = ', '.join([f':{col}' for col in columns])
            cols = ', '.join(columns)
            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            target_db.execute(text(insert_sql), dict(zip(columns, row)))

        target_db.commit()
        print(f"  {table}: Migrated {len(source_data)} rows")

    except Exception as e:
        print(f"  {table}: ERROR - {str(e)[:100]}")
        target_db.rollback()

# Update sequences to match the max IDs
print("\nUpdating sequences...")
for table in tables_order:
    try:
        # Get max ID from the table
        result = target_db.execute(text(f"SELECT MAX(id) FROM {table}")).scalar()
        if result:
            sequence_name = f"{table}_id_seq"
            target_db.execute(text(f"SELECT setval('{sequence_name}', {result}, true)"))
            print(f"  {table}_id_seq set to {result}")
    except Exception as e:
        pass  # Table might not have an id column or sequence

target_db.commit()

source_db.close()
target_db.close()

print("\n✅ Migration completed!")
