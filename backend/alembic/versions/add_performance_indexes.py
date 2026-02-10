"""add performance indexes for leads module

Revision ID: add_performance_indexes
Revises: 58527e03181f, enhance_leads_lifecycle
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = ('58527e03181f', 'enhance_leads_lifecycle')
branch_label = None
depends_on = None


def upgrade():
    """Add indexes to improve query performance"""

    # Index on leads.center_id for filtering (if not exists)
    # This speeds up: WHERE center_id = X
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_leads_center_id
        ON leads(center_id);
    """)

    # Index on children.enquiry_id for lookups (if not exists)
    # This speeds up: WHERE enquiry_id = 'TLGC####'
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_children_enquiry_id
        ON children(enquiry_id);
    """)

    # Index on parents.phone for search (if not exists)
    # This speeds up: WHERE phone LIKE '%...'
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_parents_phone
        ON parents(phone);
    """)

    # Trigram index on children.first_name for ILIKE search
    # Requires pg_trgm extension
    # This makes ILIKE searches 10-100x faster
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_children_first_name_trgm
        ON children USING gin (first_name gin_trgm_ops);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_children_last_name_trgm
        ON children USING gin (last_name gin_trgm_ops);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_parents_name_trgm
        ON parents USING gin (name gin_trgm_ops);
    """)

    # Composite index on leads for common queries
    # This speeds up: WHERE center_id = X AND status = Y
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_leads_center_status
        ON leads(center_id, status);
    """)

    # Index on intro_visits.lead_id for joins (should already exist, but ensure)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_intro_visits_lead_id
        ON intro_visits(lead_id);
    """)

    # Index on family_links.child_id for joins
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_family_links_child_id
        ON family_links(child_id);
    """)

    print("Performance indexes added successfully")


def downgrade():
    """Remove performance indexes"""

    op.execute("DROP INDEX IF EXISTS ix_leads_center_id;")
    op.execute("DROP INDEX IF EXISTS ix_children_enquiry_id;")
    op.execute("DROP INDEX IF EXISTS ix_parents_phone;")
    op.execute("DROP INDEX IF EXISTS ix_children_first_name_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_children_last_name_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_parents_name_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_leads_center_status;")
    op.execute("DROP INDEX IF EXISTS ix_intro_visits_lead_id;")
    op.execute("DROP INDEX IF EXISTS ix_family_links_child_id;")

    print("Performance indexes removed")
