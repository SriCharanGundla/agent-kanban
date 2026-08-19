"""Project Pydantic Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: str | None = Field(None, description="Project description")


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""

    name: str | None = Field(None, min_length=1, max_length=255, description="Project name")
    description: str | None = Field(None, description="Project description")


class ProjectResponse(BaseModel):
    """Schema for project in responses"""

    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectWithStats(ProjectResponse):
    """Schema for project with task statistics"""

    task_count: int = Field(..., description="Total number of tasks")
    done_count: int = Field(..., description="Number of completed tasks")
    user_role: str | None = Field(None, description="User's role in this project ('owner' or 'member')")
    member_count: int = Field(0, description="Total number of members (including owner)")
