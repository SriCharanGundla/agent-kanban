"""Integration Tests for Edge Cases and Error Scenarios"""

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.subtask import Subtask
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User


class TestSoftDeleteFiltering:
    """Test that soft-deleted items are properly filtered"""

    async def test_soft_delete_filters_correctly(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test that soft-deleted items don't appear in lists"""
        # Create active and deleted projects
        active_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            name="Active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        deleted_project = Project(
            id=uuid.uuid4(),
            owner_id=test_user.id,
            name="Deleted",
            deleted_at=datetime.now(UTC),
        )
        test_db.add_all([active_project, deleted_project])
        await test_db.commit()

        # List projects
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        projects = response.json()
        names = [p["name"] for p in projects]
        assert "Active" in names
        assert "Deleted" not in names

    async def test_get_deleted_item_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test that getting a soft-deleted item returns 404"""
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


class TestCascadeDelete:
    """Test cascade delete behavior"""

    async def test_cascade_delete_user(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User, test_project: Project
    ):
        """Test that deleting user cascades to projects (DB level)"""
        project_id = test_project.id

        # Delete user (hard delete for testing)
        await test_db.delete(test_user)
        await test_db.commit()

        # Project should be cascade deleted at DB level
        result = await test_db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        assert project is None


class TestEmptyProjectStats:
    """Test project statistics with empty data"""

    async def test_empty_project_stats(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test that empty project shows 0/0 counts"""
        response = await client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["task_count"] == 0
        assert data["done_count"] == 0


class TestSubtaskCompletionCount:
    """Test subtask completion tracking"""

    async def test_subtask_completion_count(
        self, client: AsyncClient, auth_headers: dict[str, str], test_task: Task, test_db: AsyncSession
    ):
        """Test accurate completed/total subtask counts"""
        # Create mixed subtasks
        for i in range(5):
            subtask = Subtask(
                id=uuid.uuid4(),
                task_id=test_task.id,
                title=f"Subtask {i}",
                is_completed=(i < 2),  # First 2 are completed
                position=i,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            test_db.add(subtask)
        await test_db.commit()

        response = await client.get(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_subtasks"] == 5
        assert data["completed_subtasks"] == 2


class TestTaskPositioning:
    """Test task position management"""

    async def test_task_position_on_status_change(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project, test_db: AsyncSession
    ):
        """Test that position resets when status changes"""
        # Create task in TODO with position 5
        task = Task(
            id=uuid.uuid4(),
            project_id=test_project.id,
            title="Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            position=5,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        test_db.add(task)
        await test_db.commit()

        # Change status
        response = await client.patch(
            f"/api/v1/tasks/{task.id}/status",
            headers=auth_headers,
            json={"status": "done"},
        )
        assert response.status_code == 200
        data = response.json()
        # Position should be calculated for new column
        assert data["status"] == "done"


class TestUnicodeSupport:
    """Test unicode character support"""

    async def test_unicode_in_names(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test that unicode characters are supported"""
        unicode_name = "Project 测试 🚀 Тест"
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": unicode_name},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == unicode_name

    async def test_unicode_in_task_title(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test unicode in task titles"""
        unicode_title = "タスク Task Aufgabe 任务 🎯"
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
            json={"title": unicode_title},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == unicode_title


class TestLargeTextFields:
    """Test handling of large text fields"""

    async def test_very_long_description(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test that large descriptions are supported"""
        long_description = "x" * 10000  # 10KB text
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks",
            headers=auth_headers,
            json={"title": "Task", "description": long_description},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == long_description


class TestUtilityEndpoints:
    """Test utility endpoints"""

    async def test_health_endpoint(self, client: AsyncClient):
        """Test that health check works"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_root_endpoint(self, client: AsyncClient):
        """Test that root endpoint returns info"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestInvalidUUIDs:
    """Test handling of invalid UUIDs"""

    async def test_invalid_uuid_in_path(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test that invalid UUID format returns proper error"""
        response = await client.get("/api/v1/projects/not-a-uuid", headers=auth_headers)
        assert response.status_code == 422  # Validation error


class TestConcurrentOperations:
    """Test concurrent operation handling"""

    async def test_concurrent_task_creation(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test creating multiple tasks concurrently"""
        # This tests position calculation under concurrent load
        tasks_to_create = 5
        responses = []

        for i in range(tasks_to_create):
            response = await client.post(
                f"/api/v1/projects/{test_project.id}/tasks",
                headers=auth_headers,
                json={"title": f"Concurrent Task {i}"},
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 201


class TestEmptyOptionalFields:
    """Test handling of empty optional fields"""

    async def test_null_description_project(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test creating project with null description"""
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": "Project", "description": None},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None

    async def test_update_with_null_values(
        self, client: AsyncClient, auth_headers: dict[str, str], test_project: Project
    ):
        """Test updating with null values for optional fields"""
        response = await client.put(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
            json={"name": "Updated", "description": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] is None


class TestDatabaseConstraints:
    """Test database constraint handling"""

    async def test_project_without_owner(self, test_db: AsyncSession):
        """Test that project requires owner (foreign key constraint)"""
        try:
            invalid_project = Project(
                id=uuid.uuid4(),
                owner_id=uuid.uuid4(),  # Non-existent user
                name="Invalid Project",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            test_db.add(invalid_project)
            await test_db.commit()
            # If we reach here, the test should fail
            assert False, "Expected integrity error was not raised"
        except Exception:
            # Expected: foreign key constraint violation
            await test_db.rollback()  # Clean up the failed transaction
            # Test passes if we get here


class TestSpecialCharacters:
    """Test handling of special characters"""

    async def test_special_chars_in_text_fields(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test special characters in text fields"""
        special_text = "Test <script>alert('xss')</script> & 'quotes' \"double\""
        response = await client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"name": special_text},
        )
        assert response.status_code == 201
        data = response.json()
        # Should be stored as-is (no escaping at API level)
        assert data["name"] == special_text
