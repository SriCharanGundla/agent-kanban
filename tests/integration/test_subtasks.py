"""Integration Tests for Subtasks Router"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.subtask import Subtask
from app.models.task import Task
from app.models.user import User


class TestCreateSubtask:
    """Test subtask creation endpoint"""

    async def test_create_subtask_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test successful subtask creation"""
        response = await client.post(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            headers=auth_headers,
            json={"title": "New Subtask"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Subtask"
        assert data["is_completed"] is False
        assert data["position"] == 0
        assert data["task_id"] == str(test_task.id)

    async def test_create_subtask_auto_position(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task, test_db: AsyncSession
    ):
        """Test that position auto-increments"""
        # Create first subtask
        subtask1 = Subtask(
            id=uuid.uuid4(),
            task_id=test_task.id,
            title="Subtask 1",
            is_completed=False,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(subtask1)
        await test_db.commit()

        # Create second subtask via API
        response = await client.post(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            headers=auth_headers,
            json={"title": "Subtask 2"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["position"] == 1

    async def test_create_subtask_task_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating subtask for non-existent task"""
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/tasks/{fake_id}/subtasks",
            headers=auth_headers,
            json={"title": "Subtask"},
        )
        assert response.status_code == 404

    async def test_create_subtask_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test creating subtask in another user's task"""
        # Create project and task for user2
        other_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user2.id,
            name="Other Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_project)
        await test_db.flush()

        other_task = Task(
            id=uuid.uuid4(),
            project_id=other_project.id,
            title="Other Task",
        )
        test_db.add(other_task)
        await test_db.commit()

        response = await client.post(
            f"/api/v1/tasks/{other_task.id}/subtasks",
            headers=auth_headers,
            json={"title": "Unauthorized Subtask"},
        )
        assert response.status_code == 403

    async def test_create_subtask_empty_title(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test creating subtask with empty title"""
        response = await client.post(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            headers=auth_headers,
            json={"title": ""},
        )
        assert response.status_code == 422

    async def test_create_subtask_long_title(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test creating subtask with title too long"""
        response = await client.post(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            headers=auth_headers,
            json={"title": "x" * 501},
        )
        assert response.status_code == 422

    async def test_create_subtask_no_auth(self, client: AsyncClient, test_task: Task):
        """Test creating subtask without authentication"""
        response = await client.post(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            json={"title": "Subtask"},
        )
        assert response.status_code == 401


class TestListSubtasks:
    """Test subtask listing endpoint"""

    async def test_list_subtasks_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task, test_subtask: Subtask
    ):
        """Test listing subtasks"""
        response = await client.get(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(s["id"] == str(test_subtask.id) for s in data)

    async def test_list_subtasks_empty(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test listing empty task"""
        response = await client.get(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_subtasks_ordered_by_position(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task, test_db: AsyncSession
    ):
        """Test that subtasks are ordered by position"""
        # Create subtasks with different positions
        for i in range(3):
            subtask = Subtask(
                id=uuid.uuid4(),
                task_id=test_task.id,
                title=f"Subtask {i}",
                is_completed=False,
                position=i,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            test_db.add(subtask)
        await test_db.commit()

        response = await client.get(
            f"/api/v1/tasks/{test_task.id}/subtasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        positions = [s["position"] for s in data]
        assert positions == sorted(positions)

    async def test_list_subtasks_no_auth(self, client: AsyncClient, test_task: Task):
        """Test listing subtasks without authentication"""
        response = await client.get(f"/api/v1/tasks/{test_task.id}/subtasks")
        assert response.status_code == 401


class TestUpdateSubtask:
    """Test subtask update endpoint"""

    async def test_update_subtask_title(
        self, client: AsyncClient, auth_headers: dict[str, str], test_subtask: Subtask
    ):
        """Test updating subtask title"""
        response = await client.patch(
            f"/api/v1/subtasks/{test_subtask.id}",
            headers=auth_headers,
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    async def test_update_subtask_toggle_complete(
        self, client: AsyncClient, auth_headers: dict[str, str], test_subtask: Subtask
    ):
        """Test toggling subtask completion"""
        original_status = test_subtask.is_completed

        response = await client.patch(
            f"/api/v1/subtasks/{test_subtask.id}",
            headers=auth_headers,
            json={"is_completed": not original_status},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] == (not original_status)

    async def test_update_subtask_position(
        self, client: AsyncClient, auth_headers: dict[str, str], test_subtask: Subtask
    ):
        """Test updating subtask position"""
        response = await client.patch(
            f"/api/v1/subtasks/{test_subtask.id}",
            headers=auth_headers,
            json={"position": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 5

    async def test_update_subtask_partial(
        self, client: AsyncClient, auth_headers: dict[str, str], test_subtask: Subtask
    ):
        """Test updating only some fields"""
        original_position = test_subtask.position

        response = await client.patch(
            f"/api/v1/subtasks/{test_subtask.id}",
            headers=auth_headers,
            json={"title": "New Title Only"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title Only"
        assert data["position"] == original_position

    async def test_update_subtask_all_fields(
        self, client: AsyncClient, auth_headers: dict[str, str], test_subtask: Subtask
    ):
        """Test updating all fields at once"""
        response = await client.patch(
            f"/api/v1/subtasks/{test_subtask.id}",
            headers=auth_headers,
            json={"title": "Complete Update", "is_completed": True, "position": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Complete Update"
        assert data["is_completed"] is True
        assert data["position"] == 10

    async def test_update_subtask_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test updating non-existent subtask"""
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/subtasks/{fake_id}",
            headers=auth_headers,
            json={"title": "Updated"},
        )
        assert response.status_code == 404

    async def test_update_subtask_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test updating another user's subtask"""
        # Create project, task, and subtask for user2
        other_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user2.id,
            name="Other Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_project)
        await test_db.flush()

        other_task = Task(
            id=uuid.uuid4(),
            project_id=other_project.id,
            title="Other Task",
        )
        test_db.add(other_task)
        await test_db.flush()

        other_subtask = Subtask(
            id=uuid.uuid4(),
            task_id=other_task.id,
            title="Other Subtask",
            is_completed=False,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_subtask)
        await test_db.commit()

        response = await client.patch(
            f"/api/v1/subtasks/{other_subtask.id}",
            headers=auth_headers,
            json={"title": "Hacked"},
        )
        assert response.status_code == 403

    async def test_update_subtask_no_auth(self, client: AsyncClient, test_subtask: Subtask):
        """Test updating subtask without authentication"""
        response = await client.patch(
            f"/api/v1/subtasks/{test_subtask.id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 401


class TestDeleteSubtask:
    """Test subtask deletion endpoint"""

    async def test_delete_subtask_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_subtask: Subtask, test_db: AsyncSession
    ):
        """Test hard deleting a subtask"""
        subtask_id = test_subtask.id

        response = await client.delete(f"/api/v1/subtasks/{subtask_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify subtask is hard-deleted (not in DB)
        result = await test_db.execute(select(Subtask).where(Subtask.id == subtask_id))
        subtask = result.scalar_one_or_none()
        assert subtask is None

    async def test_delete_subtask_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test deleting non-existent subtask"""
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/subtasks/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_delete_subtask_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test deleting another user's subtask"""
        # Create project, task, and subtask for user2
        other_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user2.id,
            name="Other Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_project)
        await test_db.flush()

        other_task = Task(
            id=uuid.uuid4(),
            project_id=other_project.id,
            title="Other Task",
        )
        test_db.add(other_task)
        await test_db.flush()

        other_subtask = Subtask(
            id=uuid.uuid4(),
            task_id=other_task.id,
            title="Other Subtask",
            is_completed=False,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_subtask)
        await test_db.commit()

        response = await client.delete(f"/api/v1/subtasks/{other_subtask.id}", headers=auth_headers)
        assert response.status_code == 403

    async def test_delete_subtask_no_auth(self, client: AsyncClient, test_subtask: Subtask):
        """Test deleting subtask without authentication"""
        response = await client.delete(f"/api/v1/subtasks/{test_subtask.id}")
        assert response.status_code == 401
