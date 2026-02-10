"""add lead activities table

Revision ID: add_lead_activities
Revises: add_performance_indexes
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_lead_activities'
down_revision = 'add_performance_indexes'
branch_label = None
depends_on = None


def upgrade():
    op.create_table(
        'lead_activities',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('center_id', sa.Integer(), sa.ForeignKey('centers.id'), nullable=False, index=True),
        sa.Column('activity_type', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('old_value', sa.String(200), nullable=True),
        sa.Column('new_value', sa.String(200), nullable=True),
        sa.Column('performed_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_index('ix_lead_activities_lead_performed', 'lead_activities', ['lead_id', 'performed_at'])


def downgrade():
    op.drop_index('ix_lead_activities_lead_performed', table_name='lead_activities')
    op.drop_table('lead_activities')
