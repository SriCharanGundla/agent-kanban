"""Integration Tests for Projects Router"""

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User


class TestCreateProject:
    """Test project creation endpoint"""

    async def test_create_project_success(self, client: AsyncClient, auth_headers: dict[str, str], test_user: User):
        """Test successful project creation"""
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": "New Project", "description": "Project description"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "Project description"
        assert data["owner_id"] == str(test_user.id)
        assert "id" in data
        assert "created_at" in data

    async def test_create_project_with_description(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating project with optional description"""
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": "Project Without Description"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None

    async def test_create_project_empty_name(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating project with empty name"""
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": ""},
        )
        assert response.status_code == 422

    async def test_create_project_long_name(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating project with name too long"""
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": "x" * 256},
        )
        assert response.status_code == 422

    async def test_create_project_no_auth(self, client: AsyncClient):
        """Test creating project without authentication"""
        response = await client.post(
            "/api/v1/projects",
            json={"name": "Project"},
        )
        assert response.status_code == 401

    async def test_create_project_with_api_key(self, client: AsyncClient, api_key_headers: dict[str, str]):
        """Test creating project with API key authentication"""
        response = await client.post(
            "/api/v1/projects",
            headers=api_key_headers,
            json={"name": "API Key Project"},
        )
        assert response.status_code == 201


class TestListProjects:
    """Test project listing endpoint"""

    async def test_list_projects_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test listing projects"""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert project["name"] == test_project.name

    async def test_list_projects_with_stats(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_db: AsyncSession,
    ):
        """Test that project list includes task statistics"""
        # Create some tasks
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
        task3 = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Task 3",
            status=TaskStatus.DONE,
        )
        test_db.add_all([task1, task2, task3])
        await test_db.commit()

        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        project = next((p for p in data if p["id"] == str(test_project.id)), None)
        assert project is not None
        assert project["task_count"] == 3
        assert project["done_count"] == 2

    async def test_list_projects_empty(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test listing when no projects exist"""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_projects_excludes_deleted(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test that soft-deleted projects are excluded"""
        # Create active project
        active_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            name="Active Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(active_project)

        # Create deleted project
        deleted_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            name="Deleted Project",
            deleted_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(deleted_project)
        await test_db.commit()

        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        names = [p["name"] for p in data]
        assert "Active Project" in names
        assert "Deleted Project" not in names

    async def test_list_projects_no_auth(self, client: AsyncClient):
        """Test listing projects without authentication"""
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401


class TestGetProject:
    """Test get single project endpoint"""

    async def test_get_project_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test getting a single project"""
        response = await client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_project.id)
        assert data["name"] == test_project.name
        assert "task_count" in data
        assert "done_count" in data

    async def test_get_project_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test getting non-existent project"""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/projects/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_get_project_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test getting another user's project"""
        # Create project for user2
        other_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user2.id,
            name="Other User's Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_project)
        await test_db.commit()

        # Try to get with user1's auth
        response = await client.get(f"/api/v1/projects/{other_project.id}", headers=auth_headers)
        assert response.status_code == 403

    async def test_get_project_deleted(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test getting soft-deleted project"""
        deleted_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            name="Deleted Project",
            deleted_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(deleted_project)
        await test_db.commit()

        response = await client.get(f"/api/v1/projects/{deleted_project.id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_get_project_no_auth(self, client: AsyncClient, test_project: Project):
        """Test getting project without authentication"""
        response = await client.get(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 401


class TestUpdateProject:
    """Test project update endpoint"""

    async def test_update_project_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test updating all project fields"""
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
            json={"name": "Updated Name", "description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    async def test_update_project_partial(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test updating only some fields"""
        original_description = test_project.description
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
            json={"name": "New Name Only"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name Only"
        assert data["description"] == original_description

    async def test_update_project_null_name_ignored(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test that sending name=null does not clear the project name"""
        original_name = test_project.name
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
            json={"name": None, "description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name  # Name should be unchanged
        assert data["description"] == "Updated description"

    async def test_update_project_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test updating non-existent project"""
        fake_id = uuid.uuid4()
        response = await client.put(
            f"/api/v1/projects/{fake_id}",
            headers=auth_headers,
            json={"name": "Updated"},
        )
        assert response.status_code == 404

    async def test_update_project_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test updating another user's project"""
        other_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user2.id,
            name="Other Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_project)
        await test_db.commit()

        response = await client.put(
            f"/api/v1/projects/{other_project.id}",
            headers=auth_headers,
            json={"name": "Hacked"},
        )
        assert response.status_code == 403

    async def test_update_project_no_auth(self, client: AsyncClient, test_project: Project):
        """Test updating project without authentication"""
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 401


class TestDeleteProject:
    """Test project deletion endpoint"""

    async def test_delete_project_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project, test_db: AsyncSession
    ):
        """Test soft deleting a project"""
        response = await client.delete(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify project is soft-deleted
        result = await test_db.execute(select(Project).where(Project.id == test_project.id))
        project = result.scalar_one()
        assert project.deleted_at is not None

    async def test_delete_project_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test deleting non-existent project"""
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/projects/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_delete_project_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test deleting another user's project"""
        other_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user2.id,
            name="Other Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_project)
        await test_db.commit()

        response = await client.delete(f"/api/v1/projects/{other_project.id}", headers=auth_headers)
        assert response.status_code == 403

    async def test_delete_project_no_auth(self, client: AsyncClient, test_project: Project):
        """Test deleting project without authentication"""
        response = await client.delete(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 401
