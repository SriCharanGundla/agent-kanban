"""add project members table for collaboration

Revision ID: 004
Revises: 003
Create Date: 2026-01-28 11:01:01.473881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, Sequence[str], None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enums for project_role and membership_status
    op.execute("CREATE TYPE project_role AS ENUM ('owner', 'member')")
    op.execute("CREATE TYPE membership_status AS ENUM ('pending', 'accepted')")
    
    # Create project_members table with simple columns first
    op.execute("""
        CREATE TABLE project_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            role project_role NOT NULL DEFAULT 'member',
            status membership_status NOT NULL DEFAULT 'pending',
            invitation_token VARCHAR(64) NOT NULL UNIQUE,
            invited_by_id UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            accepted_at TIMESTAMPTZ,
            CONSTRAINT uq_project_member_email UNIQUE (project_id, email)
        )
    """)
    
    # Create indexes
    op.execute("CREATE INDEX idx_project_members_project ON project_members(project_id)")
    op.execute("CREATE INDEX idx_project_members_user ON project_members(user_id) WHERE user_id IS NOT NULL")
    op.execute("CREATE INDEX idx_project_members_email ON project_members(email) WHERE status = 'pending'")
    op.execute("CREATE INDEX idx_project_members_token ON project_members(invitation_token) WHERE status = 'pending'")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop table (indexes will be dropped automatically)
    op.execute('DROP TABLE IF EXISTS project_members CASCADE')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS membership_status CASCADE')
    op.execute('DROP TYPE IF EXISTS project_role CASCADE')
