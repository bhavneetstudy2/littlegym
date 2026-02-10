"""add mdm enhancements

Revision ID: 9a3b2c1d5e6f
Revises: 76639ee9dedc
Create Date: 2026-01-26 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '9a3b2c1d5e6f'
down_revision = '76639ee9dedc'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to centers table
    with op.batch_alter_table('centers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('code', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('state', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('active', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.create_index(batch_op.f('ix_centers_code'), ['code'], unique=True)
        batch_op.create_index(batch_op.f('ix_centers_active'), ['active'], unique=False)

    # Add new columns to curricula table
    with op.batch_alter_table('curricula', schema=None) as batch_op:
        batch_op.add_column(sa.Column('level', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('age_min', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('age_max', sa.Integer(), nullable=True))

    # Create class_types table
    op.create_table('class_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('age_min', sa.Integer(), nullable=False),
        sa.Column('age_max', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='45'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_class_types_name'), 'class_types', ['name'], unique=False)
    op.create_index(op.f('ix_class_types_active'), 'class_types', ['active'], unique=False)

    # Create batch_mappings table
    op.create_table('batch_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('class_type_id', sa.Integer(), nullable=True),
        sa.Column('curriculum_id', sa.Integer(), nullable=True),
        sa.Column('center_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ),
        sa.ForeignKeyConstraint(['center_id'], ['centers.id'], ),
        sa.ForeignKeyConstraint(['class_type_id'], ['class_types.id'], ),
        sa.ForeignKeyConstraint(['curriculum_id'], ['curricula.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_batch_mappings_batch_id'), 'batch_mappings', ['batch_id'], unique=False)
    op.create_index(op.f('ix_batch_mappings_center_id'), 'batch_mappings', ['center_id'], unique=False)


def downgrade():
    # Drop batch_mappings table
    op.drop_index(op.f('ix_batch_mappings_center_id'), table_name='batch_mappings')
    op.drop_index(op.f('ix_batch_mappings_batch_id'), table_name='batch_mappings')
    op.drop_table('batch_mappings')

    # Drop class_types table
    op.drop_index(op.f('ix_class_types_active'), table_name='class_types')
    op.drop_index(op.f('ix_class_types_name'), table_name='class_types')
    op.drop_table('class_types')

    # Remove columns from curricula table
    with op.batch_alter_table('curricula', schema=None) as batch_op:
        batch_op.drop_column('age_max')
        batch_op.drop_column('age_min')
        batch_op.drop_column('level')

    # Remove columns from centers table
    with op.batch_alter_table('centers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_centers_active'))
        batch_op.drop_index(batch_op.f('ix_centers_code'))
        batch_op.drop_column('active')
        batch_op.drop_column('email')
        batch_op.drop_column('state')
        batch_op.drop_column('code')
