"""Migrate data from Supabase to Render PostgreSQL - Version 2."""
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Source: Supabase
SOURCE_DB = "postgresql+psycopg://postgres:cBS3OJZ0qMBNTV2c@db.ycmxswxwwpsbrqyycsyb.supabase.co:5432/postgres"

# Target: Render
TARGET_DB = "postgresql+psycopg://littlegym_user:4ini7p3oBDIIVmCeBRuNlKbz9uP0eGjA@dpg-d6ckulv5r7bs73agjqtg-a.singapore-postgres.render.com/littlegym"

source_engine = create_engine(SOURCE_DB)
target_engine = create_engine(TARGET_DB)

print("Starting data migration from Supabase to Render...")

# Get list of tables from target database
target_inspector = inspect(target_engine)
target_tables = target_inspector.get_table_names()

# Get list of tables from source database
source_inspector = inspect(source_engine)
source_tables = source_inspector.get_table_names()

# Find common tables (excluding alembic_version)
common_tables = [t for t in target_tables if t in source_tables and t != 'alembic_version']

print(f"\nFound {len(common_tables)} common tables to migrate")

# Order tables to handle foreign keys
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

# Filter to only tables that exist in both databases
tables_order = [t for t in tables_order if t in common_tables]

# Add any remaining common tables not in the order list
for table in common_tables:
    if table not in tables_order:
        tables_order.append(table)

print(f"Migration order: {', '.join(tables_order)}")

# Clear existing data
print("\n=== Clearing existing data ===")
with target_engine.begin() as conn:
    for table in reversed(tables_order):
        try:
            result = conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            print(f"  [OK] Cleared {table}")
        except Exception as e:
            print(f"  [ERR] {table}: {str(e)[:80]}")

# Migrate data table by table
print("\n=== Migrating data ===")
migrated_counts = {}

for table in tables_order:
    try:
        with source_engine.connect() as source_conn:
            # Get data from source
            source_data = source_conn.execute(text(f"SELECT * FROM {table}")).fetchall()

            if not source_data:
                print(f"  - {table}: No data")
                migrated_counts[table] = 0
                continue

            # Get column names
            columns = source_data[0]._fields

            # Insert into target using a transaction
            with target_engine.begin() as target_conn:
                for row in source_data:
                    placeholders = ', '.join([f':{col}' for col in columns])
                    cols = ', '.join(columns)
                    insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
                    target_conn.execute(text(insert_sql), dict(zip(columns, row)))

            migrated_counts[table] = len(source_data)
            print(f"  [OK] {table}: {len(source_data)} rows")

    except Exception as e:
        print(f"  [ERR] {table}: {str(e)[:120]}")
        migrated_counts[table] = 0

# Update sequences
print("\n=== Updating sequences ===")
with target_engine.begin() as conn:
    for table in tables_order:
        try:
            result = conn.execute(text(f"SELECT MAX(id) FROM {table}")).scalar()
            if result:
                sequence_name = f"{table}_id_seq"
                conn.execute(text(f"SELECT setval('{sequence_name}', {result}, true)"))
                print(f"  [OK] {table}_id_seq -> {result}")
        except Exception:
            pass  # Table might not have an id column

# Summary
print("\n=== Migration Summary ===")
total_rows = sum(migrated_counts.values())
successful_tables = sum(1 for c in migrated_counts.values() if c > 0)
print(f"Total tables: {len(tables_order)}")
print(f"Successful: {successful_tables}")
print(f"Total rows migrated: {total_rows}")

print("\nDone! Migration completed.")
