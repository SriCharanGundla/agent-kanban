"""Tasks Router"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUserFlexible
from app.exceptions import project_access_denied, project_not_found, task_not_found
from app.models.project import Project
from app.models.project_member import MembershipStatus, ProjectMember
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
from app.services.project_access import can_access_project

router = APIRouter(tags=["Tasks"])


async def verify_project_access(
    project_id: UUID, user_id: UUID, db: AsyncSession
) -> Project:
    """Helper function to verify project exists and user has access to it"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()

    if project is None:
        raise project_not_found()

    if not await can_access_project(db, project_id, user_id):
        raise project_access_denied()

    return project


async def verify_assignee_is_member(
    project_id: UUID, assignee_id: UUID, db: AsyncSession
) -> None:
    """Helper function to verify assignee is a project owner or accepted member"""
    # First check if assignee is the project owner
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == assignee_id,
            Project.deleted_at.is_(None),
        )
    )
    if project_result.scalar_one_or_none() is not None:
        return  # Owner is always a valid assignee

    # Otherwise, check if they're an accepted member
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == assignee_id,
            ProjectMember.status == MembershipStatus.accepted,
        )
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be an accepted member of the project",
        )


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
    # Verify project access
    await verify_project_access(project_id, current_user.id, db)

    # Get tasks with assignee relationship
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.assignee))
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
                assignee_id=task.assignee_id,
                assignee_name=task.assignee.full_name if task.assignee else None,
                created_at=task.created_at,
                updated_at=task.updated_at,
                subtasks=[
                    SubtaskResponse(
                        id=st.id,
                        task_id=st.task_id,
                        title=st.title,
                        description=st.description,
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
    # Verify project access and get project
    project = await verify_project_access(project_id, current_user.id, db)

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

    # Validate assignee is a project member if provided
    if task_data.assignee_id is not None:
        await verify_assignee_is_member(project_id, task_data.assignee_id, db)

    # Create the task
    new_task = Task(
        project_id=project_id,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        position=next_position,
        assignee_id=task_data.assignee_id,
    )

    db.add(new_task)
    
    # Update project timestamp
    now = datetime.now(UTC)
    project.updated_at = now
    
    await db.commit()
    await db.refresh(new_task)
    # Load assignee relationship if exists
    if new_task.assignee_id:
        await db.refresh(new_task, ["assignee"])

    return TaskResponse(
        id=new_task.id,
        project_id=new_task.project_id,
        title=new_task.title,
        description=new_task.description,
        status=new_task.status,
        priority=new_task.priority,
        position=new_task.position,
        assignee_id=new_task.assignee_id,
        assignee_name=new_task.assignee.full_name if new_task.assignee else None,
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
    # Get the task with assignee relationship
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.assignee))
        .where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise task_not_found()

    # Verify project ownership
    await verify_project_access(task.project_id, current_user.id, db)

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
        assignee_id=task.assignee_id,
        assignee_name=task.assignee.full_name if task.assignee else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
        subtasks=[
            SubtaskResponse(
                id=st.id,
                task_id=st.task_id,
                title=st.title,
                description=st.description,
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

    # Verify project ownership and get project
    project = await verify_project_access(task.project_id, current_user.id, db)

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
    if "assignee_id" in task_data.model_fields_set:
        # Validate assignee is a project member if setting to non-null value
        if task_data.assignee_id is not None:
            await verify_assignee_is_member(task.project_id, task_data.assignee_id, db)
        task.assignee_id = task_data.assignee_id

    now = datetime.now(UTC)
    task.updated_at = now
    project.updated_at = now

    await db.commit()
    await db.refresh(task)
    # Load assignee relationship if exists
    if task.assignee_id:
        await db.refresh(task, ["assignee"])

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee.full_name if task.assignee else None,
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

    # Verify project ownership and get project
    project = await verify_project_access(task.project_id, current_user.id, db)

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
    
    now = datetime.now(UTC)
    task.updated_at = now
    project.updated_at = now

    await db.commit()
    await db.refresh(task)
    # Load assignee relationship if exists
    if task.assignee_id:
        await db.refresh(task, ["assignee"])

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee.full_name if task.assignee else None,
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
    
    This endpoint properly handles position shifting to prevent collisions:
    - Same-column: shifts tasks between old and new position
    - Cross-column: fills gap in source column, makes room in destination
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

    # Verify project ownership and get project
    project = await verify_project_access(task.project_id, current_user.id, db)

    # Store original position and status before any changes
    old_status = task.status
    old_position = task.position
    new_status = reorder_data.status if reorder_data.status is not None else old_status
    new_position = reorder_data.position

    # Determine if this is a same-column or cross-column move
    is_same_column = old_status == new_status
    
    if is_same_column:
        # Same-column reorder: shift tasks between old and new position
        if new_position < old_position:
            # Moving up: shift tasks down to make room
            # Tasks at [new_position, old_position) increment by 1
            await db.execute(
                update(Task)
                .where(
                    Task.project_id == task.project_id,
                    Task.status == old_status,
                    Task.position >= new_position,
                    Task.position < old_position,
                    Task.id != task_id,
                    Task.deleted_at.is_(None),
                )
                .values(position=Task.position + 1)
            )
        elif new_position > old_position:
            # Moving down: shift tasks up to fill gap
            # Tasks at (old_position, new_position] decrement by 1
            await db.execute(
                update(Task)
                .where(
                    Task.project_id == task.project_id,
                    Task.status == old_status,
                    Task.position > old_position,
                    Task.position <= new_position,
                    Task.id != task_id,
                    Task.deleted_at.is_(None),
                )
                .values(position=Task.position - 1)
            )
        # If new_position == old_position, no shifting needed
    else:
        # Cross-column move
        # 1. Fill gap in source column: decrement positions after old_position
        await db.execute(
            update(Task)
            .where(
                Task.project_id == task.project_id,
                Task.status == old_status,
                Task.position > old_position,
                Task.deleted_at.is_(None),
            )
            .values(position=Task.position - 1)
        )
        
        # 2. Make room in destination column: increment positions at/after new_position
        await db.execute(
            update(Task)
            .where(
                Task.project_id == task.project_id,
                Task.status == new_status,
                Task.position >= new_position,
                Task.deleted_at.is_(None),
            )
            .values(position=Task.position + 1)
        )

    # Update the moved task's status and position
    task.status = new_status
    task.position = new_position
    
    now = datetime.now(UTC)
    task.updated_at = now
    project.updated_at = now

    await db.commit()
    await db.refresh(task)
    # Load assignee relationship if exists
    if task.assignee_id:
        await db.refresh(task, ["assignee"])

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee.full_name if task.assignee else None,
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

    # Verify project ownership and get project
    project = await verify_project_access(task.project_id, current_user.id, db)

    # Soft delete
    now = datetime.now(UTC)
    task.deleted_at = now
    project.updated_at = now
    
    await db.commit()
