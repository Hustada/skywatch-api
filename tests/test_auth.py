"""Tests for authentication endpoints and functionality."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, UTC
from sqlalchemy import select

from api.auth import get_password_hash, verify_password, hash_api_key, verify_api_key, generate_api_key
from api.models import User, ApiKey
from api.database import get_db_session


@pytest.mark.asyncio
async def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    # Hash should be different from original
    assert hashed != password
    
    # Should verify correctly
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail
    assert verify_password("wrong_password", hashed) is False


@pytest.mark.asyncio
async def test_api_key_hashing():
    """Test API key hashing with bcrypt."""
    api_key = generate_api_key()
    hashed = hash_api_key(api_key)
    
    # Hash should be different from original
    assert hashed != api_key
    
    # Should verify correctly
    assert verify_api_key(api_key, hashed) is True
    
    # Wrong key should fail
    assert verify_api_key("wrong_key", hashed) is False


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    """Test user registration endpoint."""
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "secure_password_123"
    }
    
    response = await client.post("/v1/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["name"] == user_data["name"]
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data  # Password should not be returned
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient, test_user):
    """Test that duplicate email registration fails."""
    user_data = {
        "name": "Another User",
        "email": test_user.email,  # Same email as existing user
        "password": "password123"
    }
    
    response = await client.post("/v1/auth/register", json=user_data)
    assert response.status_code == 400
    
    data = response.json()
    # Check for either old or new error format
    error_msg = data.get("detail", data.get("message", ""))
    assert "email already registered" in error_msg.lower()


@pytest.mark.asyncio
async def test_user_login(client: AsyncClient, test_user):
    """Test user login endpoint."""
    login_data = {
        "email": test_user.email,
        "password": "testpassword"  # This is the password from conftest.py
    }
    
    response = await client.post("/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password."""
    login_data = {
        "email": test_user.email,
        "password": "wrong_password"
    }
    
    response = await client.post("/v1/auth/login", json=login_data)
    assert response.status_code == 401
    
    data = response.json()
    # Check for either old or new error format
    error_msg = data.get("detail", data.get("message", ""))
    assert "incorrect email or password" in error_msg.lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "password123"
    }
    
    response = await client.post("/v1/auth/login", json=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user, auth_headers):
    """Test getting current user with JWT token."""
    response = await client.get("/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, auth_headers):
    """Test API key creation."""
    key_data = {
        "name": "Test API Key",
        "tier": "basic"
    }
    
    response = await client.post("/v1/auth/keys", json=key_data, headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "api_key" in data
    assert data["api_key"].startswith("sk_live_")
    
    key_info = data["key_info"]
    assert key_info["name"] == key_data["name"]
    assert key_info["tier"] == key_data["tier"]
    assert key_info["quota_limit"] == 10000  # Basic tier limit
    assert key_info["quota_used"] == 0
    assert key_info["is_active"] is True


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, auth_headers, test_api_key):
    """Test listing user's API keys."""
    response = await client.get("/v1/auth/keys", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Find our test key
    test_key = next((k for k in data if k["id"] == test_api_key.id), None)
    assert test_key is not None
    assert test_key["name"] == test_api_key.name
    assert test_key["tier"] == test_api_key.tier


@pytest.mark.asyncio
async def test_api_key_limit(client: AsyncClient, auth_headers, db_session):
    """Test that users cannot create more than 10 API keys."""
    # Create 10 API keys (assuming test user starts with 0)
    for i in range(10):
        key_data = {"name": f"Key {i}", "tier": "free"}
        response = await client.post("/v1/auth/keys", json=key_data, headers=auth_headers)
        assert response.status_code == 200
    
    # 11th key should fail
    key_data = {"name": "Key 11", "tier": "free"}
    response = await client.post("/v1/auth/keys", json=key_data, headers=auth_headers)
    assert response.status_code == 400
    # Check for either old or new error format
    data = response.json()
    error_msg = data.get("detail", data.get("message", ""))
    assert "maximum number of api keys" in error_msg.lower()


@pytest.mark.asyncio
async def test_deactivate_api_key(client: AsyncClient, auth_headers, test_api_key):
    """Test deactivating an API key."""
    response = await client.delete(f"/v1/auth/keys/{test_api_key.id}", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify key is deactivated
    response = await client.get("/v1/auth/keys", headers=auth_headers)
    data = response.json()
    
    # Deactivated key should not appear in active keys list
    active_key_ids = [k["id"] for k in data]
    assert test_api_key.id not in active_key_ids


@pytest.mark.asyncio
async def test_api_key_authentication(client: AsyncClient, test_api_key_string):
    """Test using API key for authentication."""
    headers = {"X-API-Key": test_api_key_string}
    
    response = await client.get("/v1/sightings", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_api_key(client: AsyncClient):
    """Test using invalid API key."""
    headers = {"X-API-Key": "sk_live_invalid_key"}
    
    response = await client.get("/v1/sightings", headers=headers)
    assert response.status_code == 401
    
    data = response.json()
    assert data["error"] == "authentication_error"
    assert "invalid or has been revoked" in data["message"]


@pytest.mark.asyncio
async def test_missing_api_key(client: AsyncClient):
    """Test request without API key."""
    response = await client.get("/v1/sightings")
    assert response.status_code == 401
    
    data = response.json()
    assert data["error"] == "authentication_error"
    assert "api key required" in data["message"].lower()


@pytest.mark.asyncio
async def test_jwt_token_expiry(client: AsyncClient, test_user):
    """Test that JWT tokens expire."""
    from api.auth import create_access_token
    
    # Create token that expires in 1 second
    token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(seconds=1)
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Should work immediately
    response = await client.get("/v1/auth/me", headers=headers)
    assert response.status_code == 200
    
    # Wait for expiry
    import asyncio
    await asyncio.sleep(2)
    
    # Should fail after expiry
    response = await client.get("/v1/auth/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_quota_tracking(client: AsyncClient, test_api_key, test_api_key_string):
    """Test that API usage counts against quota."""
    headers = {"X-API-Key": test_api_key_string}
    
    # Make a request
    response = await client.get("/v1/sightings", headers=headers)
    assert response.status_code == 200
    
    # Check quota was incremented
    async with get_db_session() as session:
        result = await session.execute(
            select(ApiKey).where(ApiKey.id == test_api_key.id)
        )
        updated_api_key = result.scalar_one()
        
        assert updated_api_key.quota_used == 1
        assert updated_api_key.last_used is not None