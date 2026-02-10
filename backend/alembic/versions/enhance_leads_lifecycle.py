"""enhance leads lifecycle

Revision ID: enhance_leads_lifecycle
Revises: 9a3b2c1d5e6f
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhance_leads_lifecycle'
down_revision = '9a3b2c1d5e6f'
branch_label = None
depends_on = None


def upgrade():
    # Step 1: Convert enum column to text
    op.execute("ALTER TABLE leads ALTER COLUMN status TYPE text USING status::text")

    # Step 2: Update text values to new names
    op.execute("UPDATE leads SET status = 'IV_SCHEDULED' WHERE status = 'INTRO_SCHEDULED'")
    op.execute("UPDATE leads SET status = 'IV_COMPLETED' WHERE status = 'INTRO_ATTENDED'")
    op.execute("UPDATE leads SET status = 'IV_NO_SHOW' WHERE status = 'NO_SHOW'")
    op.execute("UPDATE leads SET status = 'FOLLOW_UP_PENDING' WHERE status = 'FOLLOW_UP'")
    op.execute("UPDATE leads SET status = 'CLOSED_LOST' WHERE status = 'DEAD_LEAD'")
    op.execute("UPDATE leads SET status = 'ENQUIRY_RECEIVED' WHERE status = 'DISCOVERY'")

    # Step 3: Drop old enum type
    op.execute("DROP TYPE leadstatus")

    # Step 4: Create new enum type
    op.execute("""
        CREATE TYPE leadstatus AS ENUM (
            'ENQUIRY_RECEIVED',
            'DISCOVERY_COMPLETED',
            'IV_SCHEDULED',
            'IV_COMPLETED',
            'IV_NO_SHOW',
            'FOLLOW_UP_PENDING',
            'CONVERTED',
            'CLOSED_LOST'
        )
    """)

    # Step 5: Convert text column back to enum
    op.execute("ALTER TABLE leads ALTER COLUMN status TYPE leadstatus USING status::leadstatus")

    # Update LeadSource enum
    op.execute("""
        ALTER TYPE leadsource RENAME TO leadsource_old;
        CREATE TYPE leadsource AS ENUM (
            'WALK_IN',
            'PHONE_CALL',
            'ONLINE',
            'REFERRAL',
            'INSTAGRAM',
            'FACEBOOK',
            'GOOGLE',
            'OTHER'
        );
        ALTER TABLE leads ALTER COLUMN source TYPE leadsource USING source::text::leadsource;
        DROP TYPE leadsource_old;
    """)

    # Create enum types if they don't exist (checkfirst handled by IF NOT EXISTS)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ivoutcome AS ENUM (
                'INTERESTED_ENROLL_NOW',
                'INTERESTED_ENROLL_LATER',
                'NOT_INTERESTED',
                'NO_SHOW'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE followupstatus AS ENUM (
                'PENDING',
                'COMPLETED',
                'CANCELLED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE followupoutcome AS ENUM (
                'ENROLLED',
                'POSTPONED',
                'LOST',
                'SCHEDULED_IV'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Add new columns to leads table
    op.add_column('leads', sa.Column('school', sa.String(length=200), nullable=True))
    op.add_column('leads', sa.Column('preferred_schedule', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('parent_expectations', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('leads', sa.Column('discovery_completed_at', sa.Date(), nullable=True))
    op.add_column('leads', sa.Column('closed_reason', sa.String(length=500), nullable=True))
    op.add_column('leads', sa.Column('closed_at', sa.Date(), nullable=True))
    op.add_column('leads', sa.Column('enrollment_id', sa.Integer(), nullable=True))
    op.add_column('leads', sa.Column('converted_at', sa.Date(), nullable=True))

    # Rename old columns
    op.alter_column('leads', 'dead_lead_reason', new_column_name='old_dead_lead_reason')

    # Create foreign key for enrollment_id
    op.create_foreign_key('fk_leads_enrollment_id', 'leads', 'enrollments', ['enrollment_id'], ['id'])

    # Add outcome column to intro_visits (using postgresql.ENUM to avoid auto-creation)
    op.add_column('intro_visits', sa.Column('outcome', postgresql.ENUM('INTERESTED_ENROLL_NOW', 'INTERESTED_ENROLL_LATER', 'NOT_INTERESTED', 'NO_SHOW', name='ivoutcome', create_type=False), nullable=True))

    # Create follow_ups table (using postgresql.ENUM to avoid auto-creation)
    op.create_table(
        'follow_ups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('center_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'COMPLETED', 'CANCELLED', name='followupstatus', create_type=False), nullable=False),
        sa.Column('outcome', postgresql.ENUM('ENROLLED', 'POSTPONED', 'LOST', 'SCHEDULED_IV', name='followupoutcome', create_type=False), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_follow_ups_lead_id'), 'follow_ups', ['lead_id'], unique=False)
    op.create_index(op.f('ix_follow_ups_status'), 'follow_ups', ['status'], unique=False)


def downgrade():
    # Drop follow_ups table
    op.drop_index(op.f('ix_follow_ups_status'), table_name='follow_ups')
    op.drop_index(op.f('ix_follow_ups_lead_id'), table_name='follow_ups')
    op.drop_table('follow_ups')

    # Remove outcome from intro_visits
    op.drop_column('intro_visits', 'outcome')

    # Drop foreign key and new columns from leads
    op.drop_constraint('fk_leads_enrollment_id', 'leads', type_='foreignkey')
    op.drop_column('leads', 'converted_at')
    op.drop_column('leads', 'enrollment_id')
    op.drop_column('leads', 'closed_at')
    op.drop_column('leads', 'closed_reason')
    op.drop_column('leads', 'discovery_completed_at')
    op.drop_column('leads', 'parent_expectations')
    op.drop_column('leads', 'preferred_schedule')
    op.drop_column('leads', 'school')

    # Restore old column name
    op.alter_column('leads', 'old_dead_lead_reason', new_column_name='dead_lead_reason')

    # Drop new enums
    op.execute("DROP TYPE IF EXISTS followupoutcome;")
    op.execute("DROP TYPE IF EXISTS followupstatus;")
    op.execute("DROP TYPE IF EXISTS ivoutcome;")

    # Restore old enums (simplified - would need actual old values in production)
    op.execute("""
        ALTER TYPE leadsource RENAME TO leadsource_new;
        CREATE TYPE leadsource AS ENUM ('WALK_IN', 'REFERRAL', 'INSTAGRAM', 'FACEBOOK', 'GOOGLE', 'OTHER');
        ALTER TABLE leads ALTER COLUMN source TYPE leadsource USING source::text::leadsource;
        DROP TYPE leadsource_new;
    """)

    op.execute("""
        ALTER TYPE leadstatus RENAME TO leadstatus_new;
        CREATE TYPE leadstatus AS ENUM ('DISCOVERY', 'INTRO_SCHEDULED', 'INTRO_ATTENDED', 'NO_SHOW', 'FOLLOW_UP', 'DEAD_LEAD', 'ENROLLED');
        ALTER TABLE leads ALTER COLUMN status TYPE leadstatus USING status::text::leadstatus;
        DROP TYPE leadstatus_new;
    """)
