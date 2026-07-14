"""Tests for Firebase Authentication flow and endpoints."""

import pytest
from unittest.mock import patch, MagicMock
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


@patch("app.fastapi_app.services.auth_service.firebase_sign_up")
@patch("app.fastapi_app.services.auth_service.firebase_sign_in")
def test_firebase_register_success(mock_sign_in, mock_sign_up, client, enable_firebase, db_session):
    """Verify user registration under Firebase mode."""
    # Mock firebase calls
    mock_sign_up.return_value = {
        "idToken": "mock-firebase-id-token",
        "email": "newuser@example.com",
        "localId": "fb-uid-123"
    }
    mock_sign_in.return_value = {
        "idToken": "mock-firebase-id-token",
        "email": "newuser@example.com",
        "localId": "fb-uid-123",
        "expiresIn": "3600"
    }

    payload = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "full_name": "Firebase User"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert "token" in data
    assert data["token"]["access_token"] == "mock-firebase-id-token"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "Firebase User"

    # Confirm user was created in local DB
    user_repo = UserRepository(db_session)
    local_user = user_repo.get_by_email("newuser@example.com")
    assert local_user is not None
    assert local_user.full_name == "Firebase User"


@patch("app.fastapi_app.services.auth_service.firebase_sign_in")
def test_firebase_login_success(mock_sign_in, client, enable_firebase, db_session):
    """Verify user login under Firebase mode and auto-provisioning if missing locally."""
    mock_sign_in.return_value = {
        "idToken": "mock-firebase-login-token",
        "email": "existinguser@example.com",
        "localId": "fb-uid-existing",
        "expiresIn": "3600"
    }

    payload = {
        "email": "existinguser@example.com",
        "password": "mypassword"
    }

    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["access_token"] == "mock-firebase-login-token"

    # Verify user record was auto-provisioned locally
    user_repo = UserRepository(db_session)
    local_user = user_repo.get_by_email("existinguser@example.com")
    assert local_user is not None
    assert local_user.full_name == "existinguser"  # Derived from email fallback prefix


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
