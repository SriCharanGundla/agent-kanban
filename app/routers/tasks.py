"""Tasks Router"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUserFlexible
from app.exceptions import project_access_denied, project_not_found, task_not_found
from app.models.project import Project
from app.models.subtask import Subtask
from app.models.task import Task
from app.schemas.subtask import SubtaskResponse
from app.schemas.task import (
    TaskCreate,
    TaskReorderRequest,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
    TaskWithSubtasks,
)

router = APIRouter(tags=["Tasks"])


async def verify_project_ownership(
    project_id: UUID, user_id: UUID, db: AsyncSession
) -> Project:
    """Helper function to verify project exists and user owns it"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise project_not_found()

    if project.owner_id != user_id:
        raise project_access_denied()

    return project


@router.get("/projects/{project_id}/tasks", response_model=list[TaskWithSubtasks])
async def list_tasks(
    project_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
) -> list[TaskWithSubtasks]:
    """
    List all tasks in a project with their subtasks.

    Supports JWT or API Key authentication.
    Returns tasks ordered by status and position, including subtasks.
    """
    # Verify project ownership
    await verify_project_ownership(project_id, current_user.id, db)

    # Get tasks
    result = await db.execute(
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None),
        )
        .order_by(Task.status, Task.position)
        .limit(limit)
        .offset(offset)
    )
    tasks = result.scalars().all()

    # Build response with subtasks for each task
    response = []
    for task in tasks:
        # Get subtasks for this task
        subtasks_result = await db.execute(
            select(Subtask)
            .where(Subtask.task_id == task.id)
            .order_by(Subtask.position)
        )
        subtasks = subtasks_result.scalars().all()

        # Calculate subtask statistics
        completed_count = sum(1 for st in subtasks if st.is_completed)
        total_count = len(subtasks)

        response.append(
            TaskWithSubtasks(
                id=task.id,
                project_id=task.project_id,
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                position=task.position,
                created_at=task.created_at,
                updated_at=task.updated_at,
                subtasks=[
                    SubtaskResponse(
                        id=st.id,
                        task_id=st.task_id,
                        title=st.title,
                        is_completed=st.is_completed,
                        position=st.position,
                        created_at=st.created_at,
                        updated_at=st.updated_at,
                    )
                    for st in subtasks
                ],
                completed_subtasks=completed_count,
                total_subtasks=total_count,
            )
        )

    return response


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=201,
)
async def create_task(
    project_id: UUID,
    task_data: TaskCreate,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Create a new task in a project.

    Supports JWT or API Key authentication.
    Task is appended to the end of its status column.
    """
    # Verify project ownership
    await verify_project_ownership(project_id, current_user.id, db)

    # Get the next position for this status
    max_position_result = await db.execute(
        select(func.coalesce(func.max(Task.position), -1)).where(
            Task.project_id == project_id,
            Task.status == task_data.status,
            Task.deleted_at.is_(None),
        )
    )
    max_position = max_position_result.scalar_one()
    next_position = max_position + 1

    # Create the task
    new_task = Task(
        project_id=project_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        position=next_position,
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return TaskResponse(
        id=new_task.id,
        project_id=new_task.project_id,
        title=new_task.title,
        description=new_task.description,
        status=new_task.status,
        priority=new_task.priority,
        position=new_task.position,
        created_at=new_task.created_at,
        updated_at=new_task.updated_at,
    )


@router.get("/tasks/{task_id}", response_model=TaskWithSubtasks)
async def get_task(
    task_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> TaskWithSubtasks:
    """
    Get a specific task with its subtasks.

    Supports JWT or API Key authentication.
    """
    # Get the task
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise task_not_found()

    # Verify project ownership
    await verify_project_ownership(task.project_id, current_user.id, db)

    # Get subtasks
    subtasks_result = await db.execute(
        select(Subtask)
        .where(Subtask.task_id == task_id)
        .order_by(Subtask.position)
    )
    subtasks = subtasks_result.scalars().all()

    # Calculate subtask statistics
    completed_count = sum(1 for st in subtasks if st.is_completed)
    total_count = len(subtasks)

    return TaskWithSubtasks(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at,
        subtasks=[
            SubtaskResponse(
                id=st.id,
                task_id=st.task_id,
                title=st.title,
                is_completed=st.is_completed,
                position=st.position,
                created_at=st.created_at,
                updated_at=st.updated_at,
            )
            for st in subtasks
        ],
        completed_subtasks=completed_count,
        total_subtasks=total_count,
    )


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Update a task.

    Supports JWT or API Key authentication.
    """
    # Get the task
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise task_not_found()

    # Verify project ownership
    await verify_project_ownership(task.project_id, current_user.id, db)

    # Update fields if provided
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.position is not None:
        task.position = task_data.position

    task.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(task)

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID,
    status_data: TaskStatusUpdate,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Update only the status of a task.

    Supports JWT or API Key authentication.
    Task is appended to the end of the new status column.
    """
    # Get the task
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise task_not_found()

    # Verify project ownership
    await verify_project_ownership(task.project_id, current_user.id, db)

    # Get the next position for the new status
    max_position_result = await db.execute(
        select(func.coalesce(func.max(Task.position), -1)).where(
            Task.project_id == task.project_id,
            Task.status == status_data.status,
            Task.deleted_at.is_(None),
        )
    )
    max_position = max_position_result.scalar_one()

    # Update task
    task.status = status_data.status
    task.position = max_position + 1
    task.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(task)

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.patch("/tasks/{task_id}/reorder", response_model=TaskResponse)
async def reorder_task(
    task_id: UUID,
    reorder_data: TaskReorderRequest,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Reorder a task within its column or move to a different column.

    Supports JWT or API Key authentication.
    If status is provided, task is moved to that column at the specified position.
    Position is used for ordering within the status column.
    """
    # Get the task
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise task_not_found()

    # Verify project ownership
    await verify_project_ownership(task.project_id, current_user.id, db)

    # Update status if provided
    if reorder_data.status is not None:
        task.status = reorder_data.status

    # Update position
    task.position = reorder_data.position
    task.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(task)

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    current_user: CurrentUserFlexible,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft delete a task.

    Supports JWT or API Key authentication.
    """
    # Get the task
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise task_not_found()

    # Verify project ownership
    await verify_project_ownership(task.project_id, current_user.id, db)

    # Soft delete
    task.deleted_at = datetime.now(UTC)
    await db.commit()
