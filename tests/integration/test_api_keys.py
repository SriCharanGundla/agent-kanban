"""Integration Tests for API Keys Router"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.user import User


class TestCreateAPIKey:
    """Test API key creation endpoint"""

    async def test_create_api_key_success(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test successful API key creation"""
        response = await client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Test API Key"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test API Key"
        assert "api_key" in data
        assert data["api_key"].startswith("ak_")
        assert len(data["api_key"]) == 67  # "ak_" + 64 hex chars
        assert "id" in data
        assert "key_prefix" in data
        assert data["is_active"] is True

    async def test_create_api_key_empty_name(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating API key with empty name"""
        response = await client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": ""},
        )
        assert response.status_code == 422

    async def test_create_api_key_long_name(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating API key with name too long"""
        response = await client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "x" * 256},
        )
        assert response.status_code == 422

    async def test_create_api_key_requires_jwt(self, client: AsyncClient, api_key_headers: dict[str, str]):
        """Test that API key creation requires JWT, not API key auth"""
        response = await client.post(
            "/api/v1/api-keys",
            headers=api_key_headers,
            json={"name": "Test Key"},
        )
        # Should fail because API key auth is not allowed for this endpoint
        assert response.status_code == 401

    async def test_create_api_key_no_auth(self, client: AsyncClient):
        """Test creating API key without authentication"""
        response = await client.post(
            "/api/v1/api-keys",
            json={"name": "Test Key"},
        )
        assert response.status_code == 401

    async def test_create_multiple_api_keys(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test creating multiple API keys"""
        response1 = await client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Key 1"},
        )
        response2 = await client.post(
            "/api/v1/api-keys",
            headers=auth_headers,
            json={"name": "Key 2"},
        )
        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.json()["api_key"] != response2.json()["api_key"]


class TestListAPIKeys:
    """Test API key listing endpoint"""

    async def test_list_api_keys_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test listing API keys"""
        # Create some API keys
        from app.services.auth import generate_api_key, hash_api_key

        for i in range(3):
            api_key = generate_api_key()
            key_obj = ApiKey(
                id=uuid.uuid4(),
                user_id=test_user.id,
                name=f"Test Key {i}",
                key_prefix=api_key[:12],
                key_hash=hash_api_key(api_key),
                is_active=True,
                created_at=datetime.now(UTC),
            )
            test_db.add(key_obj)
        await test_db.commit()

        response = await client.get("/api/v1/api-keys", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Verify full key is not returned in list
        for key in data:
            assert "api_key" not in key
            assert "key_prefix" in key
            assert "name" in key

    async def test_list_api_keys_empty(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test listing when no API keys exist"""
        response = await client.get("/api/v1/api-keys", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_api_keys_excludes_revoked(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test that revoked keys are excluded from list"""
        from app.services.auth import generate_api_key, hash_api_key

        # Create active key
        api_key1 = generate_api_key()
        key_obj1 = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Active Key",
            key_prefix=api_key1[:12],
            key_hash=hash_api_key(api_key1),
            is_active=True,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj1)

        # Create revoked key
        api_key2 = generate_api_key()
        key_obj2 = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Revoked Key",
            key_prefix=api_key2[:12],
            key_hash=hash_api_key(api_key2),
            is_active=False,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj2)
        await test_db.commit()

        response = await client.get("/api/v1/api-keys", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active Key"

    async def test_list_api_keys_no_auth(self, client: AsyncClient):
        """Test listing API keys without authentication"""
        response = await client.get("/api/v1/api-keys")
        assert response.status_code == 401


class TestRevokeAPIKey:
    """Test API key revocation endpoint"""

    async def test_revoke_api_key_success(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test successful API key revocation"""
        from app.services.auth import generate_api_key, hash_api_key

        # Create API key
        api_key = generate_api_key()
        key_obj = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Key to Revoke",
            key_prefix=api_key[:12],
            key_hash=hash_api_key(api_key),
            is_active=True,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj)
        await test_db.commit()
        key_id = key_obj.id

        # Revoke the key
        response = await client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify key is inactive
        result = await test_db.execute(select(ApiKey).where(ApiKey.id == key_id))
        revoked_key = result.scalar_one()
        assert revoked_key.is_active is False

    async def test_revoke_api_key_not_found(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test revoking non-existent API key"""
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/api-keys/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_revoke_api_key_not_owner(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user2: User
    ):
        """Test revoking another user's API key"""
        from app.services.auth import generate_api_key, hash_api_key

        # Create API key for user2
        api_key = generate_api_key()
        key_obj = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user2.id,
            name="Other User's Key",
            key_prefix=api_key[:12],
            key_hash=hash_api_key(api_key),
            is_active=True,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj)
        await test_db.commit()
        key_id = key_obj.id

        # Try to revoke with user1's auth
        response = await client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_revoke_api_key_no_auth(self, client: AsyncClient):
        """Test revoking API key without authentication"""
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/api-keys/{fake_id}")
        assert response.status_code == 401

    async def test_revoke_already_revoked_key(
        self, client: AsyncClient, auth_headers: dict[str, str], test_db: AsyncSession, test_user: User
    ):
        """Test revoking an already revoked key"""
        from app.services.auth import generate_api_key, hash_api_key

        # Create inactive API key
        api_key = generate_api_key()
        key_obj = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Already Revoked",
            key_prefix=api_key[:12],
            key_hash=hash_api_key(api_key),
            is_active=False,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj)
        await test_db.commit()
        key_id = key_obj.id

        # Try to revoke again
        response = await client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
        assert response.status_code == 404
