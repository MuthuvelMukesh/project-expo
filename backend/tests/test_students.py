"""
Test suite for student endpoints
"""

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_get_student_profile(client, create_test_student, create_access_token):
    """Test retrieving student profile."""
    student = await create_test_student(
        email="profile@campusiq.edu",
        roll_number="CSE001",
    )
    token = create_access_token(student.user_id, "profile@campusiq.edu", "student")

    response = client.get(
        f"/api/students/{student.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["roll_number"] == "CSE001"
    assert data["cgpa"] == 8.5


@pytest.mark.asyncio
async def test_get_student_attendance(
    client, create_test_student, create_access_token
):
    """Test retrieving student attendance."""
    student = await create_test_student(email="attendance@campusiq.edu")
    token = create_access_token(
        student.user_id, "attendance@campusiq.edu", "student"
    )

    response = client.get(
        f"/api/students/{student.id}/attendance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_classes" in data
    assert "classes_attended" in data
    assert "percentage" in data


@pytest.mark.asyncio
async def test_update_student_profile(
    client, create_test_student, create_access_token
):
    """Test updating student profile."""
    student = await create_test_student(email="update@campusiq.edu", cgpa=8.0)
    token = create_access_token(student.user_id, "update@campusiq.edu", "student")

    response = client.put(
        f"/api/students/{student.id}",
        json={"cgpa": 8.5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["cgpa"] == 8.5


@pytest.mark.asyncio
async def test_get_student_predictions(
    client, create_test_student, create_access_token
):
    """Test retrieving student grade predictions."""
    student = await create_test_student(email="predictions@campusiq.edu")
    token = create_access_token(
        student.user_id, "predictions@campusiq.edu", "student"
    )

    response = client.get(
        f"/api/predictions/student/{student.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK or status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_student_dashboard(client, create_test_student, create_access_token):
    """Test student dashboard endpoint."""
    student = await create_test_student(email="dashboard@campusiq.edu")
    token = create_access_token(
        student.user_id, "dashboard@campusiq.edu", "student"
    )

    response = client.get(
        "/api/students/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
