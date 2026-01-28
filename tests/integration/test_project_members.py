"""Integration Tests for Project Members Router"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import MembershipStatus, ProjectMember, ProjectRole
from app.models.user import User


class TestListProjectMembers:
    """Test listing project members"""

    async def test_list_members_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test owner can list all members"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Check that the member is in the list
        member = next((m for m in data if m["id"] == str(test_project_member.id)), None)
        assert member is not None
        assert member["email"] == test_project_member.email

    async def test_list_members_as_member(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test member can list all members"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers_user2,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_members_as_non_member(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user3: User,
    ):
        """Test non-member cannot list members"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers_user3,
        )
        assert response.status_code == 403

    async def test_list_members_no_auth(self, client: AsyncClient, test_project: Project):
        """Test listing members without authentication"""
        response = await client.get(f"/api/v1/projects/{test_project.id}/members")
        assert response.status_code == 401

    async def test_list_members_project_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test listing members of non-existent project"""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/projects/{fake_id}/members",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestInviteProjectMember:
    """Test inviting project members"""

    async def test_invite_member_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test owner can invite a new member"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers,
            json={
                "email": "newmember@example.com",
                "role": "member",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "member" in data
        assert "invitation_link" in data
        assert data["member"]["email"] == "newmember@example.com"
        assert data["member"]["role"] == "member"
        assert data["member"]["status"] == "pending"
        assert "/invitations/" in data["invitation_link"]

    async def test_invite_member_as_owner_role(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test inviting a member with owner role"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers,
            json={
                "email": "newowner@example.com",
                "role": "owner",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["member"]["role"] == "owner"

    async def test_invite_member_existing_user(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_user2: User,
    ):
        """Test inviting an existing user"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers,
            json={
                "email": test_user2.email,
                "role": "member",
            },
        )
        # Should succeed even if user already exists
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data["member"]["email"] == test_user2.email

    async def test_invite_member_duplicate_email(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test inviting email of an already accepted member"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers,
            json={
                "email": test_project_member.email,
                "role": "member",
            },
        )
        assert response.status_code == 400
        # Since test_project_member is an accepted member, we get ALREADY_MEMBER
        assert response.json()["detail"]["code"] == "ALREADY_MEMBER"

    async def test_invite_member_as_non_owner(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test non-owner cannot invite members"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers_user2,
            json={
                "email": "another@example.com",
                "role": "member",
            },
        )
        assert response.status_code == 403

    async def test_invite_member_invalid_email(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test inviting with invalid email format"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            headers=auth_headers,
            json={
                "email": "not-an-email",
                "role": "member",
            },
        )
        assert response.status_code == 422

    async def test_invite_member_no_auth(self, client: AsyncClient, test_project: Project):
        """Test inviting without authentication"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/members",
            json={
                "email": "test@example.com",
                "role": "member",
            },
        )
        assert response.status_code == 401


class TestUpdateMemberRole:
    """Test updating project member roles"""

    async def test_update_member_role_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test owner can update member role"""
        response = await client.patch(
            f"/api/v1/projects/{test_project.id}/members/{test_project_member.id}",
            headers=auth_headers,
            json={"role": "owner"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "owner"

    async def test_update_member_role_demote_to_member(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_db: AsyncSession,
        test_user2: User,
        test_user: User,
    ):
        """Test demoting owner to member when there are other owners"""
        # First create an owner member
        owner_member = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=test_user2.id,
            email=test_user2.email,
            role=ProjectRole.owner,
            status=MembershipStatus.accepted,
            invitation_token="owner_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            accepted_at=datetime.now(UTC),
        )
        test_db.add(owner_member)
        await test_db.commit()
        await test_db.refresh(owner_member)

        # Now demote them to member (should work since original owner exists)
        response = await client.patch(
            f"/api/v1/projects/{test_project.id}/members/{owner_member.id}",
            headers=auth_headers,
            json={"role": "member"},
        )
        # This should succeed because test_user is still the original owner
        assert response.status_code == 200

    async def test_update_member_role_as_non_owner(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test non-owner cannot update member role"""
        response = await client.patch(
            f"/api/v1/projects/{test_project.id}/members/{test_project_member.id}",
            headers=auth_headers_user2,
            json={"role": "owner"},
        )
        assert response.status_code == 403

    async def test_update_member_role_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test updating non-existent member"""
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/projects/{test_project.id}/members/{fake_id}",
            headers=auth_headers,
            json={"role": "owner"},
        )
        assert response.status_code == 404


class TestRemoveProjectMember:
    """Test removing project members"""

    async def test_remove_member_as_owner(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
        test_db: AsyncSession,
    ):
        """Test owner can remove a member"""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/members/{test_project_member.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify member is deleted
        result = await test_db.execute(
            select(ProjectMember).where(ProjectMember.id == test_project_member.id)
        )
        member = result.scalar_one_or_none()
        assert member is None

    async def test_remove_self_as_member(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
        test_db: AsyncSession,
    ):
        """Test member can remove themselves"""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/members/{test_project_member.id}",
            headers=auth_headers_user2,
        )
        assert response.status_code == 204

    async def test_remove_member_cannot_remove_creator(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user2: User,
        test_db: AsyncSession,
    ):
        """Test cannot remove the original project creator"""
        # Create a member record for the original creator
        creator_member = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=test_user.id,
            email=test_user.email,
            role=ProjectRole.owner,
            status=MembershipStatus.accepted,
            invitation_token="creator_token",
            invited_by_id=test_user2.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            accepted_at=datetime.now(UTC),
        )
        test_db.add(creator_member)
        await test_db.commit()
        await test_db.refresh(creator_member)

        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/members/{creator_member.id}",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "CANNOT_REMOVE_CREATOR"

    async def test_remove_member_as_non_owner_non_self(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
        test_user3: User,
    ):
        """Test non-owner cannot remove other members"""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/members/{test_project_member.id}",
            headers=auth_headers_user3,
        )
        # User3 is not a member of the project, so should get 403
        assert response.status_code == 403

    async def test_remove_member_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test removing non-existent member"""
        fake_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/members/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_remove_member_no_auth(
        self, client: AsyncClient, test_project: Project, test_project_member: ProjectMember
    ):
        """Test removing member without authentication"""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/members/{test_project_member.id}"
        )
        assert response.status_code == 401
