"""Projects Router"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUserFlexible
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectWithStats

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
    Returns projects sorted by most recently updated.
    Includes task_count and done_count for each project.
    """
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
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None),
        )
        .order_by(Project.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return [
        ProjectWithStats(
            id=row.Project.id,
            owner_id=row.Project.owner_id,
            name=row.Project.name,
            description=row.Project.description,
            created_at=row.Project.created_at,
            updated_at=row.Project.updated_at,
            task_count=row.task_count,
            done_count=row.done_count,
        )
        for row in result.all()
    ]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify ownership
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this project",
        )

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

    return ProjectWithStats(
        id=project.id,
        owner_id=project.owner_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
        done_count=done_count,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify ownership
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this project",
        )

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


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a project.

    Supports JWT or API Key authentication.
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify ownership
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this project",
        )

    # Soft delete
    project.deleted_at = datetime.now(UTC)
    await db.commit()
