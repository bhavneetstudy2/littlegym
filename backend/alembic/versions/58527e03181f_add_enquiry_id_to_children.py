"""add_enquiry_id_to_children

Revision ID: 58527e03181f
Revises: 9a3b2c1d5e6f
Create Date: 2026-02-04 00:22:05.995357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58527e03181f'
down_revision: Union[str, None] = '9a3b2c1d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add enquiry_id column to children table
    op.add_column('children', sa.Column('enquiry_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_children_enquiry_id'), 'children', ['enquiry_id'], unique=True)


def downgrade() -> None:
    # Remove enquiry_id column from children table
    op.drop_index(op.f('ix_children_enquiry_id'), table_name='children')
    op.drop_column('children', 'enquiry_id')
