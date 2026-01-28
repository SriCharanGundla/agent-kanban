"""ProjectMember Pydantic Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.project_member import MembershipStatus, ProjectRole


class UserBasic(BaseModel):
    """Schema for basic user info"""

    id: UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class ProjectBasic(BaseModel):
    """Schema for basic project info"""

    id: UUID
    name: str
    description: str | None

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    """Schema for inviting a new member to a project"""

    email: EmailStr = Field(..., description="Email address of the person to invite")
    role: ProjectRole = Field(
        default=ProjectRole.member,
        description="Role to assign (owner or member)"
    )


class UpdateMemberRoleRequest(BaseModel):
    """Schema for updating a member's role"""

    role: ProjectRole = Field(..., description="New role to assign (owner or member)")


class ProjectMemberResponse(BaseModel):
    """Schema for project member in responses"""

    id: UUID
    project_id: UUID
    user_id: UUID | None
    email: str
    role: ProjectRole
    status: MembershipStatus
    invited_by: UserBasic
    user: UserBasic | None = Field(None, description="User details if accepted")
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}


class InviteMemberResponse(BaseModel):
    """Schema for successful invitation response"""

    member: ProjectMemberResponse
    invitation_link: str = Field(..., description="Full URL to accept the invitation")


class PendingInvitationResponse(BaseModel):
    """Schema for pending invitations for the current user"""

    id: UUID
    token: str = Field(..., description="Invitation token")
    project: ProjectBasic
    inviter: UserBasic
    role: ProjectRole
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class AcceptInvitationResponse(BaseModel):
    """Schema for successful invitation acceptance"""

    project_id: UUID = Field(..., description="ID of the project joined")
    message: str = Field(default="Invitation accepted successfully")
