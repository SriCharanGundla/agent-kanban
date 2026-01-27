"""Integration Tests for Authentication Router"""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestUserRegistration:
    """Test user registration endpoint"""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email returns error"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400
        assert "registration failed" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "password123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with password too short"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",  # Less than 8 chars
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_long_password(self, client: AsyncClient):
        """Test registration with password too long"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "x" * 101,  # More than 100 chars
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_empty_full_name(self, client: AsyncClient):
        """Test registration with empty full name"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "password123",
                "full_name": "",
            },
        )
        assert response.status_code == 422

    async def test_register_long_full_name(self, client: AsyncClient):
        """Test registration with full name too long"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "password123",
                "full_name": "x" * 256,  # More than 255 chars
            },
        )
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint"""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.email,  # OAuth2 uses 'username'
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_wrong_email(self, client: AsyncClient):
        """Test login with non-existent email"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, test_db: AsyncSession):
        """Test login with inactive user"""
        from app.services.auth import hash_password

        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            password_hash=hash_password("password123"),
            full_name="Inactive User",
            is_active=False,
        )
        test_db.add(inactive_user)
        await test_db.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "inactive@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401

    async def test_login_deleted_user(self, client: AsyncClient, test_db: AsyncSession):
        """Test login with soft-deleted user"""
        from app.services.auth import hash_password

        # Create deleted user
        deleted_user = User(
            email="deleted@example.com",
            password_hash=hash_password("password123"),
            full_name="Deleted User",
            is_active=True,
            deleted_at=datetime.now(UTC),
        )
        test_db.add(deleted_user)
        await test_db.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "deleted@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401


class TestGetCurrentUser:
    """Test get current user endpoint"""

    async def test_me_success(self, client: AsyncClient, auth_headers: dict[str, str], test_user: User):
        """Test getting current user info"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] is True
        assert "id" in data

    async def test_me_no_auth(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        """Test with invalid token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_me_malformed_auth_header(self, client: AsyncClient):
        """Test with malformed auth header"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401
