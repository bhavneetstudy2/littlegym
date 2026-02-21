"""merge heads

Revision ID: 9d68338cf2fb
Revises: add_lead_activities, add_weekly_progress_tables
Create Date: 2026-02-21 12:11:43.116295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d68338cf2fb'
down_revision: Union[str, None] = ('add_lead_activities', 'add_weekly_progress_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
