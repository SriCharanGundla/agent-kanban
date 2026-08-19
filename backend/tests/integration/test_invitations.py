"""Integration Tests for Invitations Router"""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import MembershipStatus, ProjectMember, ProjectRole
from app.models.user import User


class TestListMyInvitations:
    """Test listing user's pending invitations"""

    async def test_list_invitations_success(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test listing pending invitations for current user"""
        # Create a pending invitation for user3
        invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,  # Not accepted yet
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="test_invitation_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        test_db.add(invitation)
        await test_db.commit()

        response = await client.get("/api/v1/invitations", headers=auth_headers_user3)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        inv = next((i for i in data if i["id"] == str(invitation.id)), None)
        assert inv is not None
        assert inv["token"] == "test_invitation_token"
        assert inv["role"] == "member"
        assert "project" in inv
        assert "inviter" in inv

    async def test_list_invitations_excludes_expired(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test that expired invitations are not returned"""
        # Create an expired invitation
        expired_invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="expired_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC) - timedelta(days=8),
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
        )
        test_db.add(expired_invitation)
        await test_db.commit()

        response = await client.get("/api/v1/invitations", headers=auth_headers_user3)
        assert response.status_code == 200
        data = response.json()
        # Should not contain the expired invitation
        expired_inv = next((i for i in data if i["token"] == "expired_token"), None)
        assert expired_inv is None

    async def test_list_invitations_excludes_accepted(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test that accepted invitations are not returned"""
        response = await client.get("/api/v1/invitations", headers=auth_headers_user2)
        assert response.status_code == 200
        data = response.json()
        # Should not contain the already accepted member
        accepted = next((i for i in data if i["id"] == str(test_project_member.id)), None)
        assert accepted is None

    async def test_list_invitations_empty(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test listing invitations when there are none"""
        response = await client.get("/api/v1/invitations", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_invitations_no_auth(self, client: AsyncClient):
        """Test listing invitations without authentication"""
        response = await client.get("/api/v1/invitations")
        assert response.status_code == 401


class TestAcceptInvitation:
    """Test accepting project invitations"""

    async def test_accept_invitation_success(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test accepting a valid invitation"""
        # Create a pending invitation
        invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="accept_test_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        test_db.add(invitation)
        await test_db.commit()

        response = await client.post(
            "/api/v1/invitations/accept_test_token/accept",
            headers=auth_headers_user3,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == str(test_project.id)
        assert "message" in data

        # Verify invitation is now accepted
        result = await test_db.execute(
            select(ProjectMember).where(ProjectMember.id == invitation.id)
        )
        updated_member = result.scalar_one()
        assert updated_member.status == MembershipStatus.accepted
        assert updated_member.user_id == test_user3.id
        assert updated_member.accepted_at is not None

    async def test_accept_invitation_expired(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test accepting an expired invitation"""
        # Create an expired invitation
        invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="expired_accept_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC) - timedelta(days=8),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        test_db.add(invitation)
        await test_db.commit()

        response = await client.post(
            "/api/v1/invitations/expired_accept_token/accept",
            headers=auth_headers_user3,
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVITATION_EXPIRED"

    async def test_accept_invitation_wrong_email(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test accepting an invitation meant for a different email"""
        # Create invitation for user3
        invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="wrong_email_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        test_db.add(invitation)
        await test_db.commit()

        # Try to accept with user2's credentials
        response = await client.post(
            "/api/v1/invitations/wrong_email_token/accept",
            headers=auth_headers_user2,
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "EMAIL_MISMATCH"

    async def test_accept_invitation_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test accepting a non-existent invitation"""
        response = await client.post(
            "/api/v1/invitations/nonexistent_token/accept",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_accept_invitation_already_accepted(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test accepting an already accepted invitation"""
        # Create and immediately accept an invitation
        invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=test_user3.id,
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.accepted,
            invitation_token="already_accepted_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            accepted_at=datetime.now(UTC),
        )
        test_db.add(invitation)
        await test_db.commit()

        response = await client.post(
            "/api/v1/invitations/already_accepted_token/accept",
            headers=auth_headers_user3,
        )
        assert response.status_code == 404  # Not found because status is not pending

    async def test_accept_invitation_no_auth(self, client: AsyncClient):
        """Test accepting invitation without authentication"""
        response = await client.post("/api/v1/invitations/some_token/accept")
        assert response.status_code == 401


class TestDeclineInvitation:
    """Test declining project invitations"""

    async def test_decline_invitation_success(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test declining a valid invitation"""
        # Create a pending invitation
        invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="decline_test_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        test_db.add(invitation)
        await test_db.commit()
        invitation_id = invitation.id

        response = await client.delete(
            "/api/v1/invitations/decline_test_token",
            headers=auth_headers_user3,
        )
        assert response.status_code == 204

        # Verify invitation is deleted
        result = await test_db.execute(
            select(ProjectMember).where(ProjectMember.id == invitation_id)
        )
        deleted_member = result.scalar_one_or_none()
        assert deleted_member is None

    async def test_decline_invitation_wrong_email(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user3: User,
        test_db: AsyncSession,
    ):
        """Test declining an invitation meant for a different email"""
        # Create invitation for user3
        invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,
            email=test_user3.email,
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="decline_wrong_email_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        test_db.add(invitation)
        await test_db.commit()

        # Try to decline with user2's credentials
        response = await client.delete(
            "/api/v1/invitations/decline_wrong_email_token",
            headers=auth_headers_user2,
        )
        assert response.status_code == 403

    async def test_decline_invitation_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test declining a non-existent invitation"""
        response = await client.delete(
            "/api/v1/invitations/nonexistent_decline_token",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_decline_invitation_no_auth(self, client: AsyncClient):
        """Test declining invitation without authentication"""
        response = await client.delete("/api/v1/invitations/some_token")
        assert response.status_code == 401
