"""Add activity_categories, progression_levels, weekly_progress, child_trainer_notes tables

Revision ID: add_weekly_progress_tables
Revises: add_performance_indexes
Create Date: 2026-02-12

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_weekly_progress_tables'
down_revision = 'add_performance_indexes'
branch_label = None
depends_on = None


def upgrade():
    # activity_categories
    op.create_table('activity_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('curriculum_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category_group', sa.String(length=100), nullable=True),
        sa.Column('measurement_type', sa.Enum('LEVEL', 'COUNT', 'TIME', 'MEASUREMENT', name='measurementtype'), nullable=False, server_default='LEVEL'),
        sa.Column('measurement_unit', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['curriculum_id'], ['curricula.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_activity_categories_id', 'activity_categories', ['id'])
    op.create_index('ix_activity_categories_curriculum_id', 'activity_categories', ['curriculum_id'])

    # progression_levels
    op.create_table('progression_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('activity_category_id', sa.Integer(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['activity_category_id'], ['activity_categories.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('activity_category_id', 'level_number', name='uq_progression_level'),
    )
    op.create_index('ix_progression_levels_id', 'progression_levels', ['id'])
    op.create_index('ix_progression_levels_activity_category_id', 'progression_levels', ['activity_category_id'])

    # weekly_progress
    op.create_table('weekly_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('center_id', sa.Integer(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=True),
        sa.Column('activity_category_id', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('week_start_date', sa.Date(), nullable=False),
        sa.Column('progression_level_id', sa.Integer(), nullable=True),
        sa.Column('numeric_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id']),
        sa.ForeignKeyConstraint(['child_id'], ['children.id']),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id']),
        sa.ForeignKeyConstraint(['activity_category_id'], ['activity_categories.id']),
        sa.ForeignKeyConstraint(['progression_level_id'], ['progression_levels.id']),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('child_id', 'activity_category_id', 'week_number', 'enrollment_id', name='uq_weekly_progress_child_activity_week'),
    )
    op.create_index('ix_weekly_progress_id', 'weekly_progress', ['id'])
    op.create_index('ix_weekly_progress_center_id', 'weekly_progress', ['center_id'])
    op.create_index('ix_weekly_progress_child_id', 'weekly_progress', ['child_id'])
    op.create_index('ix_weekly_progress_enrollment_id', 'weekly_progress', ['enrollment_id'])
    op.create_index('ix_weekly_progress_activity_category_id', 'weekly_progress', ['activity_category_id'])
    op.create_index('ix_weekly_progress_child_week', 'weekly_progress', ['child_id', 'week_number'])
    op.create_index('ix_weekly_progress_activity_week', 'weekly_progress', ['activity_category_id', 'week_number'])

    # child_trainer_notes
    op.create_table('child_trainer_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('center_id', sa.Integer(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=True),
        sa.Column('parent_expectation', sa.Text(), nullable=True),
        sa.Column('progress_check', sa.Text(), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id']),
        sa.ForeignKeyConstraint(['child_id'], ['children.id']),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id']),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('child_id', 'enrollment_id', name='uq_child_trainer_notes'),
    )
    op.create_index('ix_child_trainer_notes_id', 'child_trainer_notes', ['id'])
    op.create_index('ix_child_trainer_notes_center_id', 'child_trainer_notes', ['center_id'])
    op.create_index('ix_child_trainer_notes_child_id', 'child_trainer_notes', ['child_id'])
    op.create_index('ix_child_trainer_notes_enrollment_id', 'child_trainer_notes', ['enrollment_id'])


def downgrade():
    op.drop_table('child_trainer_notes')
    op.drop_table('weekly_progress')
    op.drop_table('progression_levels')
    op.drop_table('activity_categories')
