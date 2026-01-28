"""Projects Router"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUserFlexible
from app.exceptions import project_access_denied, project_not_found
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectWithStats
from app.models.project_member import MembershipStatus, ProjectMember, ProjectRole
from app.services.project_access import (
    can_access_project,
    get_project_member_count,
    get_user_project_ids,
    get_user_role_in_project,
    is_project_owner,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectWithStats])
async def list_projects(
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
) -> list[ProjectWithStats]:
    """
    List all projects for the current user with task statistics.

    Supports JWT or API Key authentication.
    Returns projects the user owns or is a member of.
    Sorted by most recently updated.
    Includes task_count and done_count for each project.
    """
    # Get all project IDs the user has access to (owned + member)
    project_ids = await get_user_project_ids(db, current_user.id)

    if not project_ids:
        return []

    # Correlated subquery for total task count
    task_count_subq = (
        select(func.count(Task.id))
        .where(
            Task.project_id == Project.id,
            Task.deleted_at.is_(None),
        )
        .correlate(Project)
        .scalar_subquery()
    )

    # Correlated subquery for completed task count
    done_count_subq = (
        select(func.count(Task.id))
        .where(
            Task.project_id == Project.id,
            Task.status == TaskStatus.DONE,
            Task.deleted_at.is_(None),
        )
        .correlate(Project)
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            Project,
            task_count_subq.label("task_count"),
            done_count_subq.label("done_count"),
        )
        .where(
            Project.id.in_(project_ids),
            Project.deleted_at.is_(None),
        )
        .order_by(Project.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    # Fetch all rows first
    rows = result.all()
    
    if not rows:
        return []
    
    project_ids_fetched = [row.Project.id for row in rows]

    # Batch fetch: user roles for all projects
    role_result = await db.execute(
        select(ProjectMember.project_id, ProjectMember.role)
        .where(
            ProjectMember.project_id.in_(project_ids_fetched),
            ProjectMember.user_id == current_user.id,
            ProjectMember.status == MembershipStatus.accepted,
        )
    )
    user_roles_map = {r.project_id: r.role for r in role_result.all()}

    # Batch fetch: member counts for all projects
    count_result = await db.execute(
        select(
            ProjectMember.project_id,
            func.count(ProjectMember.id).label("count")
        )
        .where(
            ProjectMember.project_id.in_(project_ids_fetched),
            ProjectMember.status == MembershipStatus.accepted,
        )
        .group_by(ProjectMember.project_id)
    )
    member_counts_map = {r.project_id: r.count + 1 for r in count_result.all()}

    # Build response using maps
    projects_with_stats = []
    for row in rows:
        pid = row.Project.id
        
        # Determine role: check if owner first, then lookup in members
        if row.Project.owner_id == current_user.id:
            user_role = ProjectRole.owner
        else:
            user_role = user_roles_map.get(pid)
        
        # Member count: from map, default to 1 (just owner) if not in map
        member_count = member_counts_map.get(pid, 1)
        
        projects_with_stats.append(
            ProjectWithStats(
                id=pid,
                owner_id=row.Project.owner_id,
                name=row.Project.name,
                description=row.Project.description,
                created_at=row.Project.created_at,
                updated_at=row.Project.updated_at,
                task_count=row.task_count,
                done_count=row.done_count,
                user_role=user_role.value if user_role else None,
                member_count=member_count,
            )
        )
    
    return projects_with_stats


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Create a new project.

    Supports JWT or API Key authentication.
    """
    # Create the project
    new_project = Project(
        owner_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return ProjectResponse(
        id=new_project.id,
        owner_id=new_project.owner_id,
        name=new_project.name,
        description=new_project.description,
        created_at=new_project.created_at,
        updated_at=new_project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> ProjectWithStats:
    """
    Get a specific project with task statistics.

    Supports JWT or API Key authentication.
    Accessible by project owner and accepted members.
    """
    # Get the project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise project_not_found()

    # Verify access (owner or accepted member)
    if not await can_access_project(db, project_id, current_user.id):
        raise project_access_denied()

    # Get task statistics
    task_count_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None),
        )
    )
    task_count = task_count_result.scalar_one()

    done_count_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.project_id == project_id,
            Task.status == TaskStatus.DONE,
            Task.deleted_at.is_(None),
        )
    )
    done_count = done_count_result.scalar_one()

    # Get user's role in this project
    user_role = await get_user_role_in_project(db, project_id, current_user.id)
    
    # Get member count for this project
    member_count = await get_project_member_count(db, project_id)

    return ProjectWithStats(
        id=project.id,
        owner_id=project.owner_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
        done_count=done_count,
        user_role=user_role.value if user_role else None,
        member_count=member_count,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Update a project.

    Supports JWT or API Key authentication.
    Only project owners can update project settings.
    """
    # Get the project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise project_not_found()

    # Verify ownership (only owners can update project settings)
    if not await is_project_owner(db, project_id, current_user.id):
        raise project_access_denied()

    # Update fields that were explicitly provided (including None values)
    update_data = project_data.model_dump(exclude_unset=True)
    # Don't allow setting required 'name' field to None
    if "name" in update_data and update_data["name"] is None:
        del update_data["name"]
    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=project.id,
        owner_id=project.owner_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a project.

    Supports JWT or API Key authentication.
    Only the original project creator can delete the project.
    This marks the project as deleted but doesn't remove it from the database.
    """
    # Get the project
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise project_not_found()

    # Verify ownership - only original creator can delete
    if project.owner_id != current_user.id:
        raise project_access_denied()

    # Soft delete
    project.deleted_at = datetime.now(UTC)
    await db.commit()
