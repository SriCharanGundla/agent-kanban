"""Task Pydantic Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    """Schema for creating a new task"""

    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: str | None = Field(None, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.BACKLOG, description="Task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")


class TaskUpdate(BaseModel):
    """Schema for updating a task"""

    title: str | None = Field(None, min_length=1, max_length=500, description="Task title")
    description: str | None = Field(None, description="Task description")
    status: TaskStatus | None = Field(None, description="Task status")
    priority: TaskPriority | None = Field(None, description="Task priority")
    position: int | None = Field(None, ge=0, description="Task position in column")


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status only"""

    status: TaskStatus = Field(..., description="New task status")


class TaskReorderRequest(BaseModel):
    """Schema for reordering a task"""

    position: int = Field(..., ge=0, description="New position")
    status: TaskStatus | None = Field(None, description="Optional: move to different status column")


class TaskResponse(BaseModel):
    """Schema for task in responses"""

    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Deferred import to avoid circular dependency
def _create_task_with_subtasks():
    """Create TaskWithSubtasks class after subtask schema is available"""
    from app.schemas.subtask import SubtaskResponse

    class TaskWithSubtasks(TaskResponse):
        """Schema for task with subtasks included"""

        subtasks: list[SubtaskResponse] = Field(default_factory=list, description="List of subtasks")
        completed_subtasks: int = Field(default=0, description="Number of completed subtasks")
        total_subtasks: int = Field(default=0, description="Total number of subtasks")

    return TaskWithSubtasks


# Create the class when imported
TaskWithSubtasks = _create_task_with_subtasks()
