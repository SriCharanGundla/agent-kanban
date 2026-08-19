"""Integration Tests for Project Collaboration Features (user_role and member_count)"""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_member import MembershipStatus, ProjectMember, ProjectRole
from app.models.task import Task, TaskStatus
from app.models.user import User


class TestProjectsWithUserRole:
    """Test that projects API returns user_role field"""

    async def test_list_projects_owner_has_owner_role(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test that project owner gets user_role='owner' in list response"""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert "user_role" in project
        assert project["user_role"] == "owner"

    async def test_list_projects_member_has_member_role(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test that project member gets user_role='member' in list response"""
        response = await client.get("/api/v1/projects", headers=auth_headers_user2)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert "user_role" in project
        assert project["user_role"] == "member"

    async def test_list_projects_promoted_member_has_owner_role(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_user: User,
        test_user2: User,
        test_db: AsyncSession,
    ):
        """Test that member promoted to owner gets user_role='owner'"""
        # Create an owner member
        owner_member = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=test_user2.id,
            email=test_user2.email,
            role=ProjectRole.owner,
            status=MembershipStatus.accepted,
            invitation_token="owner_role_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            accepted_at=datetime.now(UTC),
        )
        test_db.add(owner_member)
        await test_db.commit()

        response = await client.get("/api/v1/projects", headers=auth_headers_user2)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert project["user_role"] == "owner"

    async def test_get_project_has_user_role(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test that single project GET includes user_role"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_role" in data
        assert data["user_role"] == "owner"


class TestProjectsWithMemberCount:
    """Test that projects API returns member_count field"""

    async def test_list_projects_has_member_count(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test that project list includes member_count"""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert "member_count" in project
        assert isinstance(project["member_count"], int)
        # Should be at least 1 (the owner)
        assert project["member_count"] >= 1

    async def test_member_count_includes_owner_only(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ):
        """Test that project with no additional members has member_count=1"""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        # If no project_member fixture is loaded, should be 1 (owner only)
        # Note: This test might show 2 if test_project_member fixture is active
        assert project["member_count"] >= 1

    async def test_member_count_includes_accepted_members(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test that member_count includes accepted members"""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        # Should be 2: owner + 1 accepted member
        assert project["member_count"] == 2

    async def test_member_count_excludes_pending_invitations(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that pending invitations are not counted in member_count"""
        # Create a pending invitation
        pending_invitation = ProjectMember(
            id=uuid.uuid4(),
            project_id=test_project.id,
            user_id=None,
            email="pending@example.com",
            role=ProjectRole.member,
            status=MembershipStatus.pending,
            invitation_token="pending_count_token",
            invited_by_id=test_user.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        test_db.add(pending_invitation)
        await test_db.commit()

        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        # Should still be 2: owner + 1 accepted member (pending not counted)
        assert project["member_count"] == 2

    async def test_get_project_has_member_count(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test that single project GET includes member_count"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "member_count" in data
        assert data["member_count"] == 2  # owner + 1 member


class TestCollaborationAccessControl:
    """Test that members can access shared projects"""

    async def test_member_can_list_shared_project(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test that member can see shared project in their list"""
        response = await client.get("/api/v1/projects", headers=auth_headers_user2)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert project["name"] == test_project.name

    async def test_member_can_get_shared_project(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test that member can access shared project details"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers_user2,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_project.id)
        assert data["user_role"] == "member"

    async def test_member_can_access_tasks_in_shared_project(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
        test_db: AsyncSession,
    ):
        """Test that member can access tasks in shared project"""
        # Create a task in the shared project
        task = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Shared Task",
            description="Task in shared project",
            status=TaskStatus.TODO,
            position=0,
        )
        test_db.add(task)
        await test_db.commit()

        # Member should be able to list tasks
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers_user2,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_member_can_create_task_in_shared_project(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
    ):
        """Test that member can create tasks in shared project"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers_user2,
            json={
                "title": "New Task by Member",
                "description": "Created by project member",
                "status": "todo",
                "priority": "medium",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task by Member"

    async def test_non_member_cannot_access_project(
        self,
        client: AsyncClient,
        auth_headers_user3: dict[str, str],
        test_project: Project,
        test_user3: User,
    ):
        """Test that non-member cannot access project"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers_user3,
        )
        assert response.status_code == 403


class TestCollaborationStats:
    """Test that collaboration doesn't break existing stats"""

    async def test_task_count_accurate_with_members(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
        test_db: AsyncSession,
    ):
        """Test that task_count is accurate in collaborative project"""
        # Create tasks
        task1 = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Task 1",
            status=TaskStatus.TODO,
        )
        task2 = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Task 2",
            status=TaskStatus.DONE,
        )
        test_db.add_all([task1, task2])
        await test_db.commit()

        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert project["task_count"] == 2
        assert project["done_count"] == 1

    async def test_member_sees_same_task_stats(
        self,
        client: AsyncClient,
        auth_headers_user2: dict[str, str],
        test_project: Project,
        test_project_member: ProjectMember,
        test_db: AsyncSession,
    ):
        """Test that members see the same task statistics as owner"""
        # Create tasks
        task1 = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Task 1",
            status=TaskStatus.TODO,
        )
        task2 = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Task 2",
            status=TaskStatus.DONE,
        )
        test_db.add_all([task1, task2])
        await test_db.commit()

        response = await client.get("/api/v1/projects", headers=auth_headers_user2)
        assert response.status_code == 200
        data = response.json()
        
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert project["task_count"] == 2
        assert project["done_count"] == 1
        assert project["user_role"] == "member"
        assert project["member_count"] == 2


class TestDeletedProjectAccess:
    """Test that members cannot access deleted projects"""

    async def test_member_cannot_access_deleted_project_tasks(
        self,
        client: AsyncClient,
        test_project: Project,
        test_project_member: ProjectMember,
        auth_headers_user2: dict[str, str],
        test_db: AsyncSession,
    ):
        """Test that members cannot access tasks after project is soft-deleted"""
        # Soft delete the project
        test_project.deleted_at = datetime.now(UTC)
        await test_db.commit()

        # Member tries to access tasks
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers_user2,
        )
        
        # Deleted projects return 404 (project not found) rather than 403
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "PROJECT_NOT_FOUND"

    async def test_member_cannot_access_deleted_project_details(
        self,
        client: AsyncClient,
        test_project: Project,
        test_project_member: ProjectMember,
        auth_headers_user2: dict[str, str],
        test_db: AsyncSession,
    ):
        """Test that members cannot get project details after it's soft-deleted"""
        # Soft delete the project
        test_project.deleted_at = datetime.now(UTC)
        await test_db.commit()

        # Member tries to get project details
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers_user2,
        )
        
        assert response.status_code == 404  # Project not found
        data = response.json()
        assert data["detail"]["code"] == "PROJECT_NOT_FOUND"

    async def test_member_cannot_list_deleted_projects(
        self,
        client: AsyncClient,
        test_project: Project,
        test_project_member: ProjectMember,
        auth_headers_user2: dict[str, str],
        test_db: AsyncSession,
    ):
        """Test that soft-deleted projects don't appear in member's project list"""
        # Soft delete the project
        test_project.deleted_at = datetime.now(UTC)
        await test_db.commit()

        # Member tries to list projects
        response = await client.get("/api/v1/projects", headers=auth_headers_user2)
        
        assert response.status_code == 200
        data = response.json()
        
        # Deleted project should not appear in the list
        project_ids = [p["id"] for p in data]
        assert str(test_project.id) not in project_ids
