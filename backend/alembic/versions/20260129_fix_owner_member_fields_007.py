"""fix owner member fields to null

Revision ID: 007
Revises: 006
Create Date: 2026-01-29 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, Sequence[str], None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Fix existing owner records to have NULL for invitation_token and invited_by_id
    # This corrects records that were created with the old pattern
    op.execute("""
        UPDATE project_members
        SET invitation_token = NULL,
            invited_by_id = NULL
        WHERE role = 'owner'
          AND status = 'accepted'
          AND (invitation_token IS NOT NULL OR invited_by_id IS NOT NULL)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Restore the old pattern for owner records
    # Set invitation_token to 'owner_<project_id>' and invited_by_id to user_id
    op.execute("""
        UPDATE project_members
        SET invitation_token = 'owner_' || project_id::text,
            invited_by_id = user_id
        WHERE role = 'owner'
          AND status = 'accepted'
          AND invitation_token IS NULL
          AND invited_by_id IS NULL
    """)
