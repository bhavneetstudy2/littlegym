"""add center_manager role

Revision ID: 3182b01bdc6f
Revises: 9d68338cf2fb
Create Date: 2026-02-21 12:48:53.792326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3182b01bdc6f'
down_revision: Union[str, None] = '9d68338cf2fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add CENTER_MANAGER to the userrole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'CENTER_MANAGER'")


def downgrade() -> None:
    # Cannot remove enum values in PostgreSQL easily
    pass
