"""Subtask Pydantic Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SubtaskCreate(BaseModel):
    """Schema for creating a new subtask"""

    title: str = Field(..., min_length=1, max_length=500, description="Subtask title")
    description: str | None = Field(None, max_length=5000, description="Subtask description")


class SubtaskUpdate(BaseModel):
    """Schema for updating a subtask"""

    title: str | None = Field(None, min_length=1, max_length=500, description="Subtask title")
    description: str | None = Field(None, max_length=5000, description="Subtask description")
    is_completed: bool | None = Field(None, description="Completion status")
    position: int | None = Field(None, ge=0, description="Position in list")


class SubtaskResponse(BaseModel):
    """Schema for subtask in responses"""

    id: UUID
    task_id: UUID
    title: str
    description: str | None
    is_completed: bool
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
