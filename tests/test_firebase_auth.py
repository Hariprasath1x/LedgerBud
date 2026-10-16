"""Tests for Firebase Authentication flow and endpoints."""

import pytest
from unittest.mock import patch
from fastapi import status
from fastapi.testclient import TestClient

from app.fastapi_app.main import app
from app.fastapi_app.api.deps import get_db
from app.fastapi_app.core.config import settings
from app.fastapi_app.repositories.user_repository import UserRepository


@pytest.fixture
def client(db_session):
    """Override FastAPI's db dependency to use the in-memory test db session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def enable_firebase():
    """Temporarily enable Firebase mode for testing."""
    original_use_firebase = settings.use_firebase
    original_api_key = settings.firebase_api_key
    original_project_id = settings.firebase_project_id

    settings.use_firebase = True
    settings.firebase_api_key = "test-api-key"
    settings.firebase_project_id = "test-project-id"

    yield

    settings.use_firebase = original_use_firebase
    settings.firebase_api_key = original_api_key
    settings.firebase_project_id = original_project_id


@patch("app.fastapi_app.api.deps.verify_firebase_token")
def test_firebase_update_name(mock_verify_token, client, enable_firebase, db_session):
    """Verify user can update display name with Firebase token."""
    mock_verify_token.return_value = {
        "email": "updateuser@example.com",
        "name": "Original Name",
        "uid": "fb-uid-update"
    }
    headers = {"Authorization": "Bearer valid-firebase-token"}
    # Call me first to auto-provision
    client.get("/api/v1/auth/me", headers=headers)

    # Now update name
    response = client.put("/api/v1/auth/me/name", json={"full_name": "Updated Name"}, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Name"

    # Confirm in local DB
    user_repo = UserRepository(db_session)
    local_user = user_repo.get_by_email("updateuser@example.com")
    assert local_user is not None
    assert local_user.full_name == "Updated Name"


@patch("app.fastapi_app.api.deps.verify_firebase_token")
def test_firebase_delete_profile(mock_verify_token, client, enable_firebase, db_session):
    """Verify user can delete their profile with Firebase token."""
    mock_verify_token.return_value = {
        "email": "deleteuser@example.com",
        "name": "Delete Me",
        "uid": "fb-uid-delete"
    }
    headers = {"Authorization": "Bearer valid-firebase-token"}
    # Auto-provision
    client.get("/api/v1/auth/me", headers=headers)

    with patch("firebase_admin.auth.delete_user"):
        response = client.delete("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # Confirm deleted from DB
    user_repo = UserRepository(db_session)
    local_user = user_repo.get_by_email("deleteuser@example.com")
    assert local_user is None


@patch("app.fastapi_app.api.deps.verify_firebase_token")
def test_firebase_get_me_authenticated(mock_verify_token, client, enable_firebase, db_session):
    """Verify /auth/me routes correctly with Firebase token verification and auto-provisions user."""
    mock_verify_token.return_value = {
        "email": "tokenuser@example.com",
        "name": "Token User",
        "uid": "fb-uid-token"
    }

    headers = {"Authorization": "Bearer valid-firebase-token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["email"] == "tokenuser@example.com"
    assert data["full_name"] == "Token User"

    # Confirm user exists in local database
    user_repo = UserRepository(db_session)
    local_user = user_repo.get_by_email("tokenuser@example.com")
    assert local_user is not None
    assert local_user.full_name == "Token User"
