"""Unit Tests for Authentication Service"""

import uuid
from datetime import timedelta

import pytest

from app.services.auth import (
    API_KEY_LENGTH,
    API_KEY_PREFIX,
    create_access_token,
    decode_access_token,
    extract_key_prefix,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_api_key,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password_returns_string(self):
        """Test that hashing returns a string"""
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes (salt)"""
        password = "mypassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that correct password verifies"""
        password = "mypassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that wrong password fails verification"""
        password = "mypassword"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test verification with empty password"""
        hashed = hash_password("mypassword")
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and decoding"""

    def test_create_access_token_returns_string(self):
        """Test that token creation returns a string"""
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_valid(self):
        """Test that valid token decodes to correct user_id"""
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        decoded_user_id = decode_access_token(token)
        assert decoded_user_id == user_id

    def test_decode_access_token_expired(self):
        """Test that expired token returns None"""
        user_id = uuid.uuid4()
        token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
        decoded_user_id = decode_access_token(token)
        assert decoded_user_id is None

    def test_decode_access_token_invalid(self):
        """Test that invalid token returns None"""
        decoded_user_id = decode_access_token("invalid.token.here")
        assert decoded_user_id is None

    def test_decode_access_token_malformed(self):
        """Test that malformed token returns None"""
        decoded_user_id = decode_access_token("notavalidtoken")
        assert decoded_user_id is None

    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiry"""
        user_id = uuid.uuid4()
        token = create_access_token(user_id, expires_delta=timedelta(hours=2))
        decoded_user_id = decode_access_token(token)
        assert decoded_user_id == user_id


class TestAPIKeyGeneration:
    """Test API key generation functions"""

    def test_generate_api_key_format(self):
        """Test that generated API key has correct format"""
        api_key = generate_api_key()
        assert api_key.startswith(API_KEY_PREFIX)
        # Check length: "ak_" (3 chars) + 64 hex chars = 67 total
        expected_length = len(API_KEY_PREFIX) + (API_KEY_LENGTH * 2)
        assert len(api_key) == expected_length

    def test_generate_api_key_unique(self):
        """Test that each generated key is unique"""
        keys = [generate_api_key() for _ in range(10)]
        assert len(keys) == len(set(keys))  # All unique

    def test_hash_api_key_returns_string(self):
        """Test that API key hashing returns a string"""
        api_key = generate_api_key()
        hashed = hash_api_key(api_key)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_api_key_correct(self):
        """Test that correct API key verifies"""
        api_key = generate_api_key()
        hashed = hash_api_key(api_key)
        assert verify_api_key(api_key, hashed) is True

    def test_verify_api_key_incorrect(self):
        """Test that wrong API key fails verification"""
        api_key = generate_api_key()
        wrong_key = generate_api_key()
        hashed = hash_api_key(api_key)
        assert verify_api_key(wrong_key, hashed) is False

    def test_extract_key_prefix_valid(self):
        """Test extracting prefix from valid API key"""
        api_key = generate_api_key()
        prefix = extract_key_prefix(api_key)
        assert prefix == api_key[:12]
        assert len(prefix) == 12

    def test_extract_key_prefix_invalid_format(self):
        """Test extracting prefix from invalid format returns empty"""
        invalid_key = "invalid_key_format"
        prefix = extract_key_prefix(invalid_key)
        assert prefix == ""

    def test_extract_key_prefix_empty_string(self):
        """Test extracting prefix from empty string"""
        prefix = extract_key_prefix("")
        assert prefix == ""

    def test_api_key_prefix_constant(self):
        """Test that API key prefix is correct"""
        assert API_KEY_PREFIX == "ak_"

    def test_api_key_length_constant(self):
        """Test that API key length is correct"""
        assert API_KEY_LENGTH == 32
