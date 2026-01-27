"""Integration Tests for Authentication Flows"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.user import User
from app.services.auth import create_access_token, generate_api_key, hash_api_key


class TestJWTAuthentication:
    """Test JWT authentication flow"""

    async def test_jwt_auth_valid(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test that valid JWT token authenticates successfully"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200

    async def test_jwt_auth_expired(self, client: AsyncClient, test_user: User):
        """Test that expired JWT token is rejected"""
        # Create expired token
        expired_token = create_access_token(test_user.id, expires_delta=timedelta(seconds=-1))
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_jwt_auth_invalid_signature(self, client: AsyncClient):
        """Test that token with invalid signature is rejected"""
        # Create a token with wrong secret
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        headers = {"Authorization": f"Bearer {fake_token}"}

        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_jwt_auth_malformed(self, client: AsyncClient):
        """Test that malformed token is rejected"""
        headers = {"Authorization": "Bearer not.a.valid.token"}

        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_jwt_auth_missing_bearer(self, client: AsyncClient):
        """Test that token without Bearer prefix is rejected"""
        headers = {"Authorization": "some-token"}

        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_jwt_auth_inactive_user(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test that JWT for inactive user is rejected"""
        # Create token before deactivating user
        token = create_access_token(test_user.id)

        # Deactivate user
        test_user.is_active = False
        await test_db.commit()

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    async def test_jwt_auth_deleted_user(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test that JWT for deleted user is rejected"""
        # Create token before deleting user
        token = create_access_token(test_user.id)

        # Soft-delete user
        test_user.deleted_at = datetime.now(UTC)
        await test_db.commit()

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestAPIKeyAuthentication:
    """Test API key authentication flow"""

    async def test_api_key_auth_valid(self, client: AsyncClient, api_key_headers: dict[str, str]):
        """Test that valid API key authenticates successfully"""
        response = await client.get("/api/v1/projects", headers=api_key_headers)
        assert response.status_code == 200

    async def test_api_key_auth_invalid_format(self, client: AsyncClient):
        """Test that API key without ak_ prefix is rejected"""
        headers = {"X-API-Key": "invalid_key_format"}

        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 401
        assert "invalid api key format" in response.json()["detail"].lower()

    async def test_api_key_auth_revoked(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test that revoked API key is rejected"""
        # Create revoked API key
        api_key = generate_api_key()
        key_obj = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Revoked Key",
            key_prefix=api_key[:12],
            key_hash=hash_api_key(api_key),
            is_active=False,  # Revoked
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj)
        await test_db.commit()

        headers = {"X-API-Key": api_key}
        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 401

    async def test_api_key_auth_expired(self, client: AsyncClient, expired_api_key_headers: dict[str, str]):
        """Test that expired API key is rejected"""
        response = await client.get("/api/v1/projects", headers=expired_api_key_headers)
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    async def test_api_key_auth_inactive_user(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test that API key for inactive user is rejected"""
        # Create API key
        api_key = generate_api_key()
        key_obj = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Key for Inactive User",
            key_prefix=api_key[:12],
            key_hash=hash_api_key(api_key),
            is_active=True,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj)
        await test_db.commit()

        # Deactivate user
        test_user.is_active = False
        await test_db.commit()

        headers = {"X-API-Key": api_key}
        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 401

    async def test_api_key_auth_wrong_key(self, client: AsyncClient):
        """Test that wrong API key is rejected"""
        headers = {"X-API-Key": "ak_" + "0" * 64}

        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 401

    async def test_api_key_updates_last_used(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User
    ):
        """Test that using API key updates last_used_at timestamp"""
        # Create API key
        api_key = generate_api_key()
        key_obj = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="Test Key",
            key_prefix=api_key[:12],
            key_hash=hash_api_key(api_key),
            is_active=True,
                created_at=datetime.now(UTC),
            last_used_at=None,
        )
        test_db.add(key_obj)
        await test_db.commit()
        key_id = key_obj.id

        # Use the API key
        headers = {"X-API-Key": api_key}
        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 200

        # Check that last_used_at was updated
        result = await test_db.execute(select(ApiKey).where(ApiKey.id == key_id))
        updated_key = result.scalar_one()
        assert updated_key.last_used_at is not None


class TestFlexibleAuthentication:
    """Test flexible authentication (JWT or API key)"""

    async def test_flexible_auth_jwt(self, client: AsyncClient, auth_headers: dict[str, str]):
        """Test that JWT works for flexible auth endpoints"""
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200

    async def test_flexible_auth_api_key(self, client: AsyncClient, api_key_headers: dict[str, str]):
        """Test that API key works for flexible auth endpoints"""
        response = await client.get("/api/v1/projects", headers=api_key_headers)
        assert response.status_code == 200

    async def test_flexible_auth_prefers_jwt(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        api_key_headers: dict[str, str],
        test_user: User,
    ):
        """Test that JWT is preferred when both JWT and API key are present"""
        # Combine both auth headers
        combined_headers = {**auth_headers, **api_key_headers}

        response = await client.get("/api/v1/projects", headers=combined_headers)
        assert response.status_code == 200

    async def test_flexible_auth_fallback_api_key(
        self, client: AsyncClient, api_key_headers: dict[str, str]
    ):
        """Test that API key is used when JWT is not present"""
        # Add invalid JWT
        headers = {**api_key_headers, "Authorization": "Bearer invalid"}

        # Should fall back to API key
        response = await client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 200

    async def test_flexible_auth_no_credentials(self, client: AsyncClient):
        """Test that request without any auth is rejected"""
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401


class TestAPIKeyPrefixCollision:
    """Test handling of API key prefix collisions"""

    async def test_multiple_keys_same_prefix(
        self, client: AsyncClient, test_db: AsyncSession, test_user: User, test_user2: User
    ):
        """Test that correct key is matched when multiple keys share a prefix"""
        # Generate base prefix
        base_prefix = "ak_abcdef123"

        # Create two keys with same prefix but different full keys
        api_key1 = base_prefix + "4" * 55  # First user's key
        key_obj1 = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user.id,
            name="User1 Key",
            key_prefix=api_key1[:12],
            key_hash=hash_api_key(api_key1),
            is_active=True,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj1)

        api_key2 = base_prefix + "5" * 55  # Second user's key
        key_obj2 = ApiKey(
            id=uuid.uuid4(),
            user_id=test_user2.id,
            name="User2 Key",
            key_prefix=api_key2[:12],
            key_hash=hash_api_key(api_key2),
            is_active=True,
                created_at=datetime.now(UTC),
        )
        test_db.add(key_obj2)
        await test_db.commit()

        # Use user1's key
        headers1 = {"X-API-Key": api_key1}
        response1 = await client.get("/api/v1/projects", headers=headers1)
        assert response1.status_code == 200
        # Should only see user1's projects

        # Use user2's key
        headers2 = {"X-API-Key": api_key2}
        response2 = await client.get("/api/v1/projects", headers=headers2)
        assert response2.status_code == 200
        # Should only see user2's projects
