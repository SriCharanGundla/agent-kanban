"""Invitations Router - Handle invitation acceptance and management"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import CurrentUserFlexible
from app.exceptions import (
    already_member,
    email_mismatch,
    invitation_expired,
    invitation_not_found,
)
from app.models.project_member import MembershipStatus, ProjectMember
from app.schemas.project_member import AcceptInvitationResponse, PendingInvitationResponse

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.get("", response_model=list[PendingInvitationResponse])
async def list_my_invitations(
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> list[PendingInvitationResponse]:
    """
    List all pending invitations for the current user.
    
    Returns invitations that:
    - Match the current user's email
    - Have status 'pending'
    - Have not expired
    """
    now = datetime.now(UTC)
    
    result = await db.execute(
        select(ProjectMember)
        .where(
            ProjectMember.email == current_user.email,
            ProjectMember.status == MembershipStatus.pending,
            ProjectMember.expires_at > now,
        )
        .options(
            selectinload(ProjectMember.project),
            selectinload(ProjectMember.invited_by),
        )
        .order_by(ProjectMember.created_at.desc())
    )
    invitations = result.scalars().all()

    return [
        PendingInvitationResponse(
            id=inv.id,
            token=inv.invitation_token,
            project={
                "id": inv.project.id,
                "name": inv.project.name,
                "description": inv.project.description,
            },
            inviter={
                "id": inv.invited_by.id,
                "full_name": inv.invited_by.full_name,
                "email": inv.invited_by.email,
            },
            role=inv.role,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
        )
        for inv in invitations
    ]


@router.post("/{token}/accept", response_model=AcceptInvitationResponse)
async def accept_invitation(
    token: str,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> AcceptInvitationResponse:
    """
    Accept a project invitation by token.
    
    Validates:
    - Token exists and not expired
    - Invitation email matches current user's email
    - User is not already a member
    """
    now = datetime.now(UTC)

    # Get the invitation
    result = await db.execute(
        select(ProjectMember)
        .where(
            ProjectMember.invitation_token == token,
            ProjectMember.status == MembershipStatus.pending,
        )
        .options(selectinload(ProjectMember.project))
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise invitation_not_found()

    # Check if expired
    if invitation.expires_at <= now:
        raise invitation_expired()

    # Validate email matches
    if invitation.email != current_user.email:
        raise email_mismatch()

    # Check if user is already a member (shouldn't happen, but defensive check)
    if invitation.user_id and invitation.status == MembershipStatus.accepted:
        raise already_member()

    # Accept the invitation
    invitation.user_id = current_user.id
    invitation.status = MembershipStatus.accepted
    invitation.accepted_at = now

    await db.commit()
    await db.refresh(invitation)

    return AcceptInvitationResponse(
        project_id=invitation.project_id,
        message="Invitation accepted successfully",
    )


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def decline_invitation(
    token: str,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Decline a project invitation by token.
    
    Validates:
    - Token exists
    - Invitation email matches current user's email
    
    Deletes the invitation record.
    """
    # Get the invitation
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.invitation_token == token,
            ProjectMember.status == MembershipStatus.pending,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise invitation_not_found()

    # Validate email matches
    if invitation.email != current_user.email:
        raise email_mismatch()

    # Delete the invitation
    await db.delete(invitation)
    await db.commit()
