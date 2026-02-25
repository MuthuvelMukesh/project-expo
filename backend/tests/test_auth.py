"""
Test suite for authentication endpoints
"""

import pytest
from fastapi import status


@pytest.mark.auth
@pytest.mark.asyncio
async def test_register_student(client, db_session):
    """Test student registration endpoint."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newstudent@campusiq.edu",
            "password": "securepass123",
            "role": "student",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newstudent@campusiq.edu"
    assert "id" in data
    assert "access_token" in data


@pytest.mark.auth
@pytest.mark.asyncio
async def test_register_duplicate_email(client, create_test_user):
    """Test that duplicate emails are rejected."""
    # Create initial user
    await create_test_user(email="duplicate@campusiq.edu")

    # Try to register with same email
    response = client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@campusiq.edu",
            "password": "securepass123",
            "role": "student",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.auth
@pytest.mark.asyncio
async def test_login_success(client, create_test_user):
    """Test successful login."""
    user = await create_test_user(
        email="logintest@campusiq.edu",
        password="correctpassword123",
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "logintest@campusiq.edu",
            "password": "correctpassword123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "logintest@campusiq.edu"


@pytest.mark.auth
@pytest.mark.asyncio
async def test_login_wrong_password(client, create_test_user):
    """Test login with wrong password."""
    await create_test_user(
        email="wrongpass@campusiq.edu",
        password="correctpassword",
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@campusiq.edu",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Test login with nonexistent email."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@campusiq.edu",
            "password": "anypassword",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
@pytest.mark.asyncio
async def test_change_password(client, create_test_user, create_access_token):
    """Test password change endpoint."""
    user = await create_test_user(
        email="changepass@campusiq.edu",
        password="oldpassword123",
    )
    token = create_access_token(user.id, user.email, "student")

    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Try logging in with new password
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "changepass@campusiq.edu",
            "password": "newpassword123",
        },
    )
    assert login_response.status_code == status.HTTP_200_OK
