"""Pytest Configuration and Fixtures"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.api_key import ApiKey
from app.models.base import Base
from app.models.project import Project
from app.models.project_member import MembershipStatus, ProjectMember, ProjectRole
from app.models.subtask import Subtask
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.services.auth import create_access_token, generate_api_key, hash_api_key, hash_password


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine"""
    # Use TEST_DATABASE_URL for tests - must be set in .env
    if not settings.TEST_DATABASE_URL:
        raise ValueError(
            "TEST_DATABASE_URL must be set in .env file for running tests. "
            "This should point to a separate test database, not your production database."
        )
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override"""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)  # type: ignore
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def test_user2(test_db: AsyncSession) -> User:
    """Create a second test user for ownership tests"""
    user = User(
        id=uuid.uuid4(),
        email="test2@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User 2",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def test_user3(test_db: AsyncSession) -> User:
    """Create a third test user for collaboration tests"""
    user = User(
        id=uuid.uuid4(),
        email="test3@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User 3",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict[str, str]:
    """Create JWT authentication headers"""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_user2(test_user2: User) -> dict[str, str]:
    """Create JWT authentication headers for test_user2"""
    token = create_access_token(test_user2.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_user3(test_user3: User) -> dict[str, str]:
    """Create JWT authentication headers for test_user3"""
    token = create_access_token(test_user3.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
async def api_key_headers(test_user: User, test_db: AsyncSession) -> dict[str, str]:
    """Create API key authentication headers"""
    api_key = generate_api_key()
    key_prefix = api_key[:12]

    api_key_obj = ApiKey(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Test API Key",
        key_prefix=key_prefix,
        key_hash=hash_api_key(api_key),
        is_active=True,
        created_at=datetime.now(UTC),
        expires_at=None,
    )
    test_db.add(api_key_obj)
    await test_db.commit()

    return {"X-API-Key": api_key}


@pytest.fixture(scope="function")
async def expired_api_key_headers(test_user: User, test_db: AsyncSession) -> dict[str, str]:
    """Create expired API key authentication headers"""
    api_key = generate_api_key()
    key_prefix = api_key[:12]

    api_key_obj = ApiKey(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Expired API Key",
        key_prefix=key_prefix,
        key_hash=hash_api_key(api_key),
        is_active=True,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired yesterday
    )
    test_db.add(api_key_obj)
    await test_db.commit()

    return {"X-API-Key": api_key}


@pytest.fixture(scope="function")
async def test_project(test_user: User, test_db: AsyncSession) -> Project:
    """Create a test project"""
    from app.models.project_member import ProjectMember, ProjectRole, MembershipStatus
    
    project = Project(
        id=uuid.uuid4(),
        owner_id=test_user.id,
        name="Test Project",
        description="Test project description",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_db.add(project)
    await test_db.flush()
    
    # Create owner as a project member (matching the API behavior)
    owner_member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        email=test_user.email,
        role=ProjectRole.owner,
        status=MembershipStatus.accepted,
        invitation_token=None,
        invited_by_id=None,
        expires_at=None,
        accepted_at=datetime.now(UTC),
    )
    test_db.add(owner_member)
    
    await test_db.commit()
    await test_db.refresh(project)
    return project


@pytest.fixture(scope="function")
async def test_task(test_project: Project, test_db: AsyncSession) -> Task:
    """Create a test task"""
    task = Task(
        id=uuid.uuid4(),
        project_id=test_project.id,
        title="Test Task",
        description="Test task description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        position=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)
    return task


@pytest.fixture(scope="function")
async def test_subtask(test_task: Task, test_db: AsyncSession) -> Subtask:
    """Create a test subtask"""
    subtask = Subtask(
        id=uuid.uuid4(),
        task_id=test_task.id,
        title="Test Subtask",
        is_completed=False,
        position=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    test_db.add(subtask)
    await test_db.commit()
    await test_db.refresh(subtask)
    return subtask


@pytest.fixture(scope="function")
async def test_project_member(
    test_project: Project, test_user2: User, test_user: User, test_db: AsyncSession
) -> ProjectMember:
    """Create an accepted project member"""
    member = ProjectMember(
        id=uuid.uuid4(),
        project_id=test_project.id,
        user_id=test_user2.id,
        email=test_user2.email,
        role=ProjectRole.member,
        status=MembershipStatus.accepted,
        invitation_token="test_token_accepted",
        invited_by_id=test_user.id,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=7),
        accepted_at=datetime.now(UTC),
    )
    test_db.add(member)
    await test_db.commit()
    await test_db.refresh(member)
    return member
