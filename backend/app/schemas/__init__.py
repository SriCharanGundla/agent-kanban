"""Pydantic Schemas"""

from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyResponse,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectWithStats,
)
from app.schemas.project_member import (
    AcceptInvitationResponse,
    InviteMemberRequest,
    InviteMemberResponse,
    PendingInvitationResponse,
    ProjectMemberResponse,
    UpdateMemberRoleRequest,
)
from app.schemas.subtask import (
    SubtaskCreate,
    SubtaskResponse,
    SubtaskUpdate,
)
from app.schemas.task import (
    TaskCreate,
    TaskReorderRequest,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
    TaskWithSubtasks,
)
from app.schemas.user import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "Token",
    # API Key schemas
    "ApiKeyCreate",
    "ApiKeyResponse",
    "ApiKeyCreateResponse",
    # Project schemas
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectWithStats",
    # Project Member schemas
    "InviteMemberRequest",
    "InviteMemberResponse",
    "ProjectMemberResponse",
    "UpdateMemberRoleRequest",
    "PendingInvitationResponse",
    "AcceptInvitationResponse",
    # Task schemas
    "TaskCreate",
    "TaskUpdate",
    "TaskStatusUpdate",
    "TaskReorderRequest",
    "TaskResponse",
    "TaskWithSubtasks",
    # Subtask schemas
    "SubtaskCreate",
    "SubtaskUpdate",
    "SubtaskResponse",
]
