"""Project Members Router - Manage project collaboration"""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUserFlexible
from app.exceptions import (
    already_member,
    cannot_remove_creator,
    invitation_already_sent,
    last_owner,
    member_not_found,
    project_access_denied,
    project_not_found,
)
from app.models.project import Project
from app.models.project_member import MembershipStatus, ProjectMember, ProjectRole
from app.models.user import User
from app.schemas.project_member import (
    InviteMemberRequest,
    InviteMemberResponse,
    ProjectMemberResponse,
    UpdateMemberRoleRequest,
)
from app.services.project_access import is_project_owner

router = APIRouter(tags=["Project Members"])


def generate_invitation_token() -> str:
    """Generate a secure random invitation token"""
    return secrets.token_urlsafe(32)


def get_invitation_link(token: str) -> str:
    """Generate the full invitation link URL"""
    # Use the frontend URL from settings or default
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:7654')
    return f"{frontend_url}/invitations/{token}"


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectMemberResponse]:
    """
    List all members of a project.
    
    Accessible by any project member (owner or accepted member).
    Returns all members including pending invitations.
    """
    # Verify project exists
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise project_not_found()

    # Check if user has access to the project
    from app.services.project_access import can_access_project
    if not await can_access_project(db, project_id, current_user.id):
        raise project_access_denied()

    # Get all members with related data
    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .options(
            selectinload(ProjectMember.invited_by),
            selectinload(ProjectMember.user),
        )
        .order_by(ProjectMember.created_at)
    )
    members = result.scalars().all()

    return members


@router.post("/projects/{project_id}/members", response_model=InviteMemberResponse)
async def invite_project_member(
    project_id: UUID,
    invite_request: InviteMemberRequest,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> InviteMemberResponse:
    """
    Invite a new member to the project by email.
    
    Only project owners can invite members.
    Generates a unique invitation link that expires in 7 days.
    """
    # Verify project exists
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise project_not_found()

    # Check if user is an owner
    if not await is_project_owner(db, project_id, current_user.id):
        raise project_access_denied()

    # Check if email is already invited or is a member
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.email == invite_request.email,
        )
    )
    existing_member = result.scalar_one_or_none()
    if existing_member:
        if existing_member.status == MembershipStatus.accepted:
            raise already_member()
        else:
            raise invitation_already_sent()

    # Check if user exists in the database
    result = await db.execute(
        select(User).where(User.email == invite_request.email)
    )
    invited_user = result.scalar_one_or_none()

    # Generate invitation token and expiry
    token = generate_invitation_token()
    expires_at = datetime.now(UTC) + timedelta(days=7)

    # Create project member record
    new_member = ProjectMember(
        project_id=project_id,
        user_id=invited_user.id if invited_user else None,
        email=invite_request.email,
        role=invite_request.role,
        status=MembershipStatus.pending,
        invitation_token=token,
        invited_by_id=current_user.id,
        expires_at=expires_at,
    )

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    # Load relationships
    await db.refresh(new_member, ["invited_by", "user"])

    # Generate invitation link
    invitation_link = get_invitation_link(token)

    return InviteMemberResponse(
        member=ProjectMemberResponse.model_validate(new_member),
        invitation_link=invitation_link,
    )


@router.patch("/projects/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
async def update_member_role(
    project_id: UUID,
    member_id: UUID,
    role_update: UpdateMemberRoleRequest,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberResponse:
    """
    Update a project member's role.
    
    Only project owners can update member roles.
    Cannot demote yourself if you're the last owner.
    """
    # Verify project exists
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise project_not_found()

    # Check if user is an owner
    if not await is_project_owner(db, project_id, current_user.id):
        raise project_access_denied()

    # Get the member to update
    result = await db.execute(
        select(ProjectMember)
        .where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        )
        .options(
            selectinload(ProjectMember.invited_by),
            selectinload(ProjectMember.user),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise member_not_found()

    # If demoting from owner to member, check if they're the last owner
    if member.role == ProjectRole.owner and role_update.role == ProjectRole.member:
        # Count other owners
        result = await db.execute(
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == ProjectRole.owner,
                ProjectMember.status == MembershipStatus.accepted,
                ProjectMember.id != member_id,
            )
        )
        other_owners = result.scalars().all()
        
        # Check if project owner_id is different from member's user_id
        is_last_owner = len(other_owners) == 0 and project.owner_id == member.user_id
        
        if is_last_owner:
            raise last_owner()

    # Update the role
    member.role = role_update.role
    await db.commit()
    await db.refresh(member)

    return member


@router.delete("/projects/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: UUID,
    member_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove a member from the project.
    
    Project owners can remove any member.
    Members can remove themselves.
    Cannot remove the original project creator.
    """
    # Verify project exists
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise project_not_found()

    # Get the member to remove
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise member_not_found()

    # Check permissions
    is_owner = await is_project_owner(db, project_id, current_user.id)
    is_self_removal = member.user_id == current_user.id

    if not (is_owner or is_self_removal):
        raise project_access_denied()

    # Prevent removing the original project creator
    if member.user_id == project.owner_id:
        raise cannot_remove_creator()

    # Delete the member
    await db.delete(member)
    await db.commit()
