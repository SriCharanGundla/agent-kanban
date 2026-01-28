"""Project Access Service - Authorization helpers for project collaboration"""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import MembershipStatus, ProjectMember, ProjectRole


async def can_access_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Check if a user can access a project.
    Returns True if the user is either:
    - The project owner (owner_id matches)
    - An accepted member of the project
    """
    # Check if user is the owner
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if project:
        return True

    # Check if user is an accepted member of a non-deleted project
    result = await db.execute(
        select(ProjectMember)
        .join(Project, ProjectMember.project_id == Project.id)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.status == MembershipStatus.accepted,
            Project.deleted_at.is_(None),
        )
    )
    member = result.scalar_one_or_none()
    return member is not None


async def is_project_owner(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Check if a user is a project owner.
    Returns True if the user is either:
    - The original project creator (owner_id matches)
    - An accepted member with the 'owner' role
    """
    # Check if user is the original owner
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if project:
        return True

    # Check if user is an accepted member with owner role
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.role == ProjectRole.owner,
            ProjectMember.status == MembershipStatus.accepted,
        )
    )
    member = result.scalar_one_or_none()
    return member is not None


async def get_user_project_ids(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[uuid.UUID]:
    """
    Get all project IDs that a user has access to.
    Includes:
    - Projects where user is the owner
    - Projects where user is an accepted member
    """
    # Get owned projects
    result = await db.execute(
        select(Project.id).where(
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
        )
    )
    owned_ids = [row[0] for row in result.all()]

    # Get member projects
    result = await db.execute(
        select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id,
            ProjectMember.status == MembershipStatus.accepted,
        )
    )
    member_ids = [row[0] for row in result.all()]

    # Combine and deduplicate
    all_ids = list(set(owned_ids + member_ids))
    return all_ids


async def get_user_role_in_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProjectRole | None:
    """
    Get the user's role in a project.
    Returns:
    - ProjectRole.owner if user is the original owner or has owner role as member
    - ProjectRole.member if user is an accepted member with member role
    - None if user has no access to the project
    """
    # Check if user is the original owner
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == user_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if project:
        return ProjectRole.owner

    # Check member role
    result = await db.execute(
        select(ProjectMember.role).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.status == MembershipStatus.accepted,
        )
    )
    role = result.scalar_one_or_none()
    return role


async def get_project_member_count(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> int:
    """
    Get the total number of members in a project.
    Returns the count of accepted members + 1 for the original owner.
    """
    from sqlalchemy import func

    # Count accepted members
    result = await db.execute(
        select(func.count(ProjectMember.id)).where(
            ProjectMember.project_id == project_id,
            ProjectMember.status == MembershipStatus.accepted,
        )
    )
    accepted_count = result.scalar_one()
    
    # +1 for the original owner (who may or may not be in members table)
    return accepted_count + 1
