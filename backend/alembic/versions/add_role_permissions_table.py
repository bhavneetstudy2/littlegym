"""Add role_permissions table for configurable RBAC

Revision ID: add_role_permissions_table
Revises: 3182b01bdc6f
Create Date: 2026-03-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_role_permissions_table'
down_revision = '3182b01bdc6f'
branch_label = None
depends_on = None


def upgrade():
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('center_id', sa.Integer(), sa.ForeignKey('centers.id'), nullable=False, index=True),
        sa.Column('role', sa.Enum('SUPER_ADMIN', 'CENTER_ADMIN', 'CENTER_MANAGER', 'TRAINER', 'COUNSELOR', name='userrole', create_type=False), nullable=False),
        sa.Column('permission_key', sa.String(100), nullable=False),
        sa.Column('is_allowed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('center_id', 'role', 'permission_key', name='uq_center_role_permission'),
    )


def downgrade():
    op.drop_table('role_permissions')
