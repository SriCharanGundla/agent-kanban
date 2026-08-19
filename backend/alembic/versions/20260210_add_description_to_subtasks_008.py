"""add description to subtasks

Revision ID: 008
Revises: 007
Create Date: 2026-02-10 15:09:19.619726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, Sequence[str], None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add description column to subtasks table
    op.add_column('subtasks', sa.Column('description', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove description column from subtasks table
    op.drop_column('subtasks', 'description')
