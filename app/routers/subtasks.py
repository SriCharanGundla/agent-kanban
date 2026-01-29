"""Subtasks Router"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUserFlexible
from app.exceptions import subtask_not_found, task_access_denied, task_not_found
from app.models.project import Project
from app.models.subtask import Subtask
from app.models.task import Task
from app.schemas.subtask import SubtaskCreate, SubtaskResponse, SubtaskUpdate
from app.services.project_access import can_access_project

router = APIRouter(tags=["Subtasks"])


async def verify_task_ownership(task_id: UUID, user_id: UUID, db: AsyncSession) -> tuple[Task, Project]:
    """Helper function to verify task exists and user has access to it through project"""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise task_not_found()

    # Verify project access (owner or accepted member)
    if not await can_access_project(db, task.project_id, user_id):
        raise task_access_denied()

    # Fetch the project (already verified via can_access_project)
    result = await db.execute(
        select(Project).where(
            Project.id == task.project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one()  # Safe - access was already verified

    return task, project


@router.get("/tasks/{task_id}/subtasks", response_model=list[SubtaskResponse])
async def list_subtasks(
    task_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
) -> list[SubtaskResponse]:
    """
    List all subtasks for a task.

    Supports JWT or API Key authentication.
    Returns subtasks ordered by position.
    """
    # Verify task ownership
    _, _ = await verify_task_ownership(task_id, current_user.id, db)

    # Get subtasks
    result = await db.execute(
        select(Subtask)
        .where(Subtask.task_id == task_id)
        .order_by(Subtask.position)
        .limit(limit)
        .offset(offset)
    )
    subtasks = result.scalars().all()

    return [
        SubtaskResponse(
            id=subtask.id,
            task_id=subtask.task_id,
            title=subtask.title,
            is_completed=subtask.is_completed,
            position=subtask.position,
            created_at=subtask.created_at,
            updated_at=subtask.updated_at,
        )
        for subtask in subtasks
    ]


@router.post(
    "/tasks/{task_id}/subtasks",
    response_model=SubtaskResponse,
    status_code=201,
)
async def create_subtask(
    task_id: UUID,
    subtask_data: SubtaskCreate,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> SubtaskResponse:
    """
    Create a new subtask for a task.

    Supports JWT or API Key authentication.
    Subtask is appended to the end of the list.
    """
    # Verify task ownership and get task and project
    task, project = await verify_task_ownership(task_id, current_user.id, db)

    # Get the next position
    max_position_result = await db.execute(
        select(func.coalesce(func.max(Subtask.position), -1)).where(
            Subtask.task_id == task_id
        )
    )
    max_position = max_position_result.scalar_one()
    next_position = max_position + 1

    # Create the subtask
    new_subtask = Subtask(
        task_id=task_id,
        title=subtask_data.title,
        is_completed=False,
        position=next_position,
    )

    db.add(new_subtask)
    
    # Update project timestamp
    now = datetime.now(UTC)
    project.updated_at = now
    
    await db.commit()
    await db.refresh(new_subtask)

    return SubtaskResponse(
        id=new_subtask.id,
        task_id=new_subtask.task_id,
        title=new_subtask.title,
        is_completed=new_subtask.is_completed,
        position=new_subtask.position,
        created_at=new_subtask.created_at,
        updated_at=new_subtask.updated_at,
    )


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    subtask_id: UUID,
    subtask_data: SubtaskUpdate,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> SubtaskResponse:
    """
    Update a subtask (title, completion status, or position).

    Supports JWT or API Key authentication.
    """
    # Get the subtask
    result = await db.execute(select(Subtask).where(Subtask.id == subtask_id))
    subtask = result.scalar_one_or_none()

    if subtask is None:
        raise subtask_not_found()

    # Verify task ownership and get task and project
    task, project = await verify_task_ownership(subtask.task_id, current_user.id, db)

    # Update fields if provided
    if subtask_data.title is not None:
        subtask.title = subtask_data.title
    if subtask_data.is_completed is not None:
        subtask.is_completed = subtask_data.is_completed
    if subtask_data.position is not None:
        subtask.position = subtask_data.position

    now = datetime.now(UTC)
    subtask.updated_at = now
    project.updated_at = now

    await db.commit()
    await db.refresh(subtask)

    return SubtaskResponse(
        id=subtask.id,
        task_id=subtask.task_id,
        title=subtask.title,
        is_completed=subtask.is_completed,
        position=subtask.position,
        created_at=subtask.created_at,
        updated_at=subtask.updated_at,
    )


@router.delete("/subtasks/{subtask_id}", status_code=204)
async def delete_subtask(
    subtask_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a subtask (hard delete).

    Supports JWT or API Key authentication.
    """
    # Get the subtask
    result = await db.execute(select(Subtask).where(Subtask.id == subtask_id))
    subtask = result.scalar_one_or_none()

    if subtask is None:
        raise subtask_not_found()

    # Verify task ownership and get task and project
    task, project = await verify_task_ownership(subtask.task_id, current_user.id, db)

    # Hard delete (subtasks don't have soft delete)
    await db.delete(subtask)
    
    # Update project timestamp
    now = datetime.now(UTC)
    project.updated_at = now
    
    await db.commit()
