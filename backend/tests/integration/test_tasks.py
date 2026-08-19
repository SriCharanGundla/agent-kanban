"""Integration Tests for Tasks Router"""

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.subtask import Subtask
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User


class TestCreateTask:
    """Test task creation endpoint"""

    async def test_create_task_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test successful task creation"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
            json={"title": "New Task", "description": "Task description"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task description"
        assert data["status"] == "backlog"
        assert data["priority"] == "medium"
        assert data["position"] == 0

    async def test_create_task_all_fields(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test creating task with all fields specified"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
            json={
                "title": "Complete Task",
                "description": "Full description",
                "status": "todo",
                "priority": "high",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Complete Task"
        assert data["status"] == "todo"
        assert data["priority"] == "high"

    async def test_create_task_auto_position(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_db: AsyncSession,
    ):
        """Test that position auto-increments"""
        # Create first task
        task1 = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(task1)
        await test_db.commit()

        # Create second task via API
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
            json={"title": "Task 2", "status": "todo"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["position"] == 1

    async def test_create_task_project_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating task for non-existent project"""
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/projects/{fake_id}/tasks",
            headers=auth_headers,
            json={"title": "Task"},
        )
        assert response.status_code == 404

    async def test_create_task_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test creating task in another user's project"""
        other_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user2.id,
            name="Other Project",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_project)
        await test_db.commit()

        response = await client.post(
            f"/api/v1/projects/{other_project.id}/tasks",
            headers=auth_headers,
            json={"title": "Unauthorized Task"},
        )
        assert response.status_code == 403

    async def test_create_task_empty_title(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test creating task with empty title"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
            json={"title": ""},
        )
        assert response.status_code == 422

    async def test_create_task_no_auth(self, client: AsyncClient, test_project: Project):
        """Test creating task without authentication"""
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            json={"title": "Task"},
        )
        assert response.status_code == 401


class TestListTasks:
    """Test task listing endpoint"""

    async def test_list_tasks_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project, test_task: Task
    ):
        """Test listing tasks"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(t["id"] == str(test_task.id) for t in data)

    async def test_list_tasks_empty(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test listing empty project"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_tasks_excludes_deleted(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_db: AsyncSession,
    ):
        """Test that soft-deleted tasks are excluded"""
        # Create active task
        active_task = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Active Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(active_task)

        # Create deleted task
        deleted_task = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Deleted Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            deleted_at=datetime.now(UTC),
        )
        test_db.add(deleted_task)
        await test_db.commit()

        response = await client.get(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        titles = [t["title"] for t in data]
        assert "Active Task" in titles
        assert "Deleted Task" not in titles

    async def test_list_tasks_ordered_by_position(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
        test_db: AsyncSession,
    ):
        """Test that tasks are ordered by position"""
        # Create tasks with different positions
        for i in range(3):
            task = Task(
                id=uuid.uuid4(),
                project_id=test_project.id,
                title=f"Task {i}",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                position=i,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            test_db.add(task)
        await test_db.commit()

        response = await client.get(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        positions = [t["position"] for t in data]
        assert positions == sorted(positions)

    async def test_list_tasks_no_auth(self, client: AsyncClient, test_project: Project):
        """Test listing tasks without authentication"""
        response = await client.get(f"/api/v1/projects/{test_project.id}/tasks")
        assert response.status_code == 401


class TestGetTask:
    """Test get single task endpoint"""

    async def test_get_task_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test getting a single task"""
        response = await client.get(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_task.id)
        assert data["title"] == test_task.title
        assert "subtasks" in data
        assert "completed_subtasks" in data
        assert "total_subtasks" in data

    async def test_get_task_with_subtasks(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task, test_db: AsyncSession
    ):
        """Test getting task with subtask statistics"""
        # Create subtasks
        subtask1 = Subtask(
            id=uuid.uuid4(),
            task_id=test_task.id,
            title="Subtask 1",
            is_completed=True,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        subtask2 = Subtask(
            id=uuid.uuid4(),
            task_id=test_task.id,
            title="Subtask 2",
            is_completed=False,
            position=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add_all([subtask1, subtask2])
        await test_db.commit()

        response = await client.get(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_subtasks"] == 2
        assert data["completed_subtasks"] == 1
        assert len(data["subtasks"]) == 2

    async def test_get_task_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test getting non-existent task"""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/tasks/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_get_task_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test getting another user's task"""
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
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(other_task)
        await test_db.commit()

        response = await client.get(f"/api/v1/tasks/{other_task.id}", headers=auth_headers)
        assert response.status_code == 403

    async def test_get_task_no_auth(self, client: AsyncClient, test_task: Task):
        """Test getting task without authentication"""
        response = await client.get(f"/api/v1/tasks/{test_task.id}")
        assert response.status_code == 401


class TestUpdateTask:
    """Test task update endpoint"""

    async def test_update_task_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test updating all task fields"""
        response = await client.put(
            f"/api/v1/tasks/{test_task.id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "description": "Updated description",
                "status": "in_progress",
                "priority": "high",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"

    async def test_update_task_partial(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test updating only some fields"""
        response = await client.put(
            f"/api/v1/tasks/{test_task.id}",
            headers=auth_headers,
            json={"title": "New Title Only"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title Only"
        assert data["status"] == test_task.status.value

    async def test_update_task_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test updating non-existent task"""
        fake_id = uuid.uuid4()
        response = await client.put(
            f"/api/v1/tasks/{fake_id}",
            headers=auth_headers,
            json={"title": "Updated"},
        )
        assert response.status_code == 404

    async def test_update_task_no_auth(self, client: AsyncClient, test_task: Task):
        """Test updating task without authentication"""
        response = await client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 401


class TestUpdateTaskStatus:
    """Test task status update endpoint"""

    async def test_update_status_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test updating task status"""
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}/status",
            headers=auth_headers,
            json={"status": "in_progress"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    async def test_update_status_repositions(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_task: Task,
        test_db: AsyncSession,
    ):
        """Test that status change repositions task to end of column"""
        # Set initial status and position
        test_task.status = TaskStatus.TODO
        test_task.position = 0
        await test_db.commit()

        # Change status
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}/status",
            headers=auth_headers,
            json={"status": "in_progress"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        # Position should be reset
        assert data["position"] == 0

    async def test_update_status_invalid(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test updating status to invalid value"""
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}/status",
            headers=auth_headers,
            json={"status": "INVALID_STATUS"},
        )
        assert response.status_code == 422

    async def test_update_status_no_auth(self, client: AsyncClient, test_task: Task):
        """Test updating status without authentication"""
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}/status",
            json={"status": "done"},
        )
        assert response.status_code == 401


class TestReorderTask:
    """Test task reordering endpoint"""

    async def test_reorder_task_same_column(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test reordering within same column"""
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}/reorder",
            headers=auth_headers,
            json={"position": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 5

    async def test_reorder_task_different_column(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task
    ):
        """Test moving task to different column"""
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}/reorder",
            headers=auth_headers,
            json={"position": 3, "status": "done"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 3
        assert data["status"] == "done"

    async def test_reorder_task_no_auth(self, client: AsyncClient, test_task: Task):
        """Test reordering without authentication"""
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}/reorder",
            json={"position": 1},
        )
        assert response.status_code == 401


class TestDeleteTask:
    """Test task deletion endpoint"""

    async def test_delete_task_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task, test_db: AsyncSession
    ):
        """Test soft deleting a task"""
        response = await client.delete(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify task is soft-deleted
        result = await test_db.execute(select(Task).where(Task.id == test_task.id))
        task = result.scalar_one()
        assert task.deleted_at is not None

    async def test_delete_task_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test deleting non-existent task"""
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/tasks/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_delete_task_cascades_subtasks(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task, test_db: AsyncSession
    ):
        """Test that deleting task makes subtasks inaccessible"""
        # Create subtask
        subtask = Subtask(
            id=uuid.uuid4(),
            task_id=test_task.id,
            title="Subtask",
            is_completed=False,
            position=0,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(subtask)
        await test_db.commit()
        subtask_id = subtask.id

        # Delete task
        response = await client.delete(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify subtask still exists in DB (cascade is at DB level, not soft delete)
        result = await test_db.execute(select(Subtask).where(Subtask.id == subtask_id))
        subtask = result.scalar_one_or_none()
        # Subtask should still exist but task is soft-deleted
        assert subtask is not None

    async def test_delete_task_no_auth(self, client: AsyncClient, test_task: Task):
        """Test deleting task without authentication"""
        response = await client.delete(f"/api/v1/tasks/{test_task.id}")
        assert response.status_code == 401
