"""add task assignee field

Revision ID: 005
Revises: 004
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add assignee_id column to tasks table
    op.add_column('tasks', sa.Column('assignee_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_tasks_assignee', 'tasks', 'users', ['assignee_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_tasks_assignee_id'), 'tasks', ['assignee_id'], unique=False)


def downgrade() -> None:
    # Remove the assignee_id column
    op.drop_index(op.f('ix_tasks_assignee_id'), table_name='tasks')
    op.drop_constraint('fk_tasks_assignee', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'assignee_id')
