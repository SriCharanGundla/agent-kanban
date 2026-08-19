"""make owner a real member

Revision ID: 006
Revises: 005
Create Date: 2026-01-29 05:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, Sequence[str], None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Make expires_at nullable
    op.execute("ALTER TABLE project_members ALTER COLUMN expires_at DROP NOT NULL")
    
    # Step 2: Make invited_by_id nullable (needed for self-invitation pattern)
    op.execute("ALTER TABLE project_members ALTER COLUMN invited_by_id DROP NOT NULL")
    
    # Step 3: Make invitation_token nullable (owner doesn't need a real invitation token)
    op.execute("ALTER TABLE project_members ALTER COLUMN invitation_token DROP NOT NULL")
    
    # Step 4: Backfill owner members for all existing projects
    op.execute("""
        INSERT INTO project_members (
            id, project_id, user_id, email, role, status, 
            invitation_token, invited_by_id, created_at, expires_at, accepted_at
        )
        SELECT 
            gen_random_uuid(),
            p.id,
            p.owner_id,
            u.email,
            'owner',
            'accepted',
            NULL,
            NULL,
            p.created_at,
            NULL,
            p.created_at
        FROM projects p
        JOIN users u ON u.id = p.owner_id
        WHERE p.deleted_at IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM project_members pm 
            WHERE pm.project_id = p.id AND pm.user_id = p.owner_id AND pm.status = 'accepted'
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove owner member entries (those with NULL invitation_token and invited_by_id)
    op.execute("""
        DELETE FROM project_members 
        WHERE invitation_token IS NULL 
        AND invited_by_id IS NULL 
        AND role = 'owner'
    """)
    
    # Restore NOT NULL constraints (this will fail if there are NULL values)
    op.execute("ALTER TABLE project_members ALTER COLUMN invitation_token SET NOT NULL")
    op.execute("ALTER TABLE project_members ALTER COLUMN invited_by_id SET NOT NULL")
    op.execute("ALTER TABLE project_members ALTER COLUMN expires_at SET NOT NULL")
