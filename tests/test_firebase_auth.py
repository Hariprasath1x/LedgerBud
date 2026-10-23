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


def test_unauthenticated_request_rejected(client):
    """Unauthenticated requests to protected endpoints are rejected with 401 Unauthorized."""
    endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/wallets"),
        ("GET", "/api/v1/transactions"),
        ("GET", "/api/v1/budgets"),
        ("GET", "/api/v1/goals"),
        ("GET", "/api/v1/subscriptions"),
        ("GET", "/api/v1/net-worth/summary"),
        ("GET", "/api/v1/dashboard"),
        ("POST", "/api/v1/advisor/ask"),
        ("GET", "/api/v1/fire"),
    ]
    for method, path in endpoints:
        resp = client.request(method, path)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json()["detail"] == "Not authenticated"


@patch("app.fastapi_app.api.deps.verify_firebase_token")
def test_invalid_or_expired_token_rejected(mock_verify_token, client, enable_firebase):
    """Tokens that fail signature verification or are expired are rejected with 401."""
    from app.fastapi_app.core.exceptions import AuthenticationError

    mock_verify_token.side_effect = AuthenticationError("Token validation failed (SDK: Token expired)")
    headers = {"Authorization": "Bearer expired-token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Firebase authentication failed" in response.json()["detail"]


def test_use_firebase_false_rejects_bearer_token(client):
    """When USE_FIREBASE=false, verify_id_token is not initialized and token requests are rejected."""
    headers = {"Authorization": "Bearer some-token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("app.fastapi_app.api.deps.verify_firebase_token")
def test_cross_user_resource_isolation_transactions(mock_verify_token, client, enable_firebase, db_session):
    """User A cannot read, update, or delete User B's transactions or wallets."""
    from datetime import date
    from app.fastapi_app.models.user import User
    from app.fastapi_app.models.wallet import Wallet
    from app.fastapi_app.models.transaction import Transaction

    # Seed User B and User B's transaction
    user_b = User(full_name="User B", email="userb@example.com", firebase_uid="fb-b", password_hash="hash", is_active=True)
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    wallet_b = Wallet(user_id=user_b.id, wallet_name="B Wallet", wallet_type="bank", balance=500.0)
    db_session.add(wallet_b)
    db_session.commit()
    db_session.refresh(wallet_b)

    txn_b = Transaction(
        user_id=user_b.id,
        wallet_id=wallet_b.id,
        amount=100.0,
        merchant_name="Merchant B",
        transaction_type="Expense",
        transaction_date=date(2026, 7, 1),
    )
    db_session.add(txn_b)
    db_session.commit()
    db_session.refresh(txn_b)

    # Act as User A
    mock_verify_token.return_value = {
        "email": "usera@example.com",
        "name": "User A",
        "uid": "fb-a",
    }
    headers = {"Authorization": "Bearer token-a"}

    # 1. User A listing transactions should not see User B's transaction
    list_resp = client.get("/api/v1/transactions", headers=headers)
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["total"] == 0

    # 2. User A updating User B's transaction returns 404
    update_resp = client.put(f"/api/v1/transactions/{txn_b.id}", json={"amount": 200.0}, headers=headers)
    assert update_resp.status_code == status.HTTP_404_NOT_FOUND

    # 3. User A deleting User B's transaction returns 404
    delete_resp = client.delete(f"/api/v1/transactions/{txn_b.id}", headers=headers)
    assert delete_resp.status_code == status.HTTP_404_NOT_FOUND

    # 4. User A updating User B's wallet returns 404
    update_w_resp = client.put(f"/api/v1/wallets/{wallet_b.id}", json={"wallet_name": "Stolen"}, headers=headers)
    assert update_w_resp.status_code == status.HTTP_404_NOT_FOUND
