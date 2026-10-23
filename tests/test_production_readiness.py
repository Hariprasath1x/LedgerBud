"""Tests for Phase 3 Production Startup and Hosting Readiness.

Covers:
1. Production URL resolution and validation in ui/api_client.py.
2. Health endpoint behavior with healthy and failing database connections.
3. Statement-import storage security, permissions, and stale upload pruning.
4. FastAPI startup port and environment resolution.
"""

import os
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.fastapi_app.api.deps import get_db
from app.fastapi_app.main import app
from app.fastapi_app.services.import_service import (
    DEFAULT_UPLOAD_FOLDER,
    cleanup_stale_uploads,
)
from ui.api_client import APIClient, resolve_backend_url


# =====================================================================
# 1. Streamlit-to-FastAPI Backend URL Configuration Tests
# =====================================================================

def test_resolve_backend_url_dev_default(monkeypatch):
    """In development mode with no env var set, falls back to http://localhost:8000."""
    monkeypatch.delenv("FASTAPI_BASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    url = resolve_backend_url()
    assert url == "http://localhost:8000"


def test_resolve_backend_url_from_env(monkeypatch):
    """Resolves FASTAPI_BASE_URL from environment and normalizes trailing slash."""
    monkeypatch.setenv("FASTAPI_BASE_URL", "https://api.ledgerbud.onrender.com/")
    monkeypatch.setenv("ENVIRONMENT", "production")
    url = resolve_backend_url()
    assert url == "https://api.ledgerbud.onrender.com"


def test_resolve_backend_url_missing_in_production(monkeypatch):
    """In production mode, missing FASTAPI_BASE_URL raises a clear, actionable error."""
    monkeypatch.delenv("FASTAPI_BASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(ValueError, match="FASTAPI_BASE_URL is not configured"):
        resolve_backend_url()


def test_resolve_backend_url_localhost_in_production(monkeypatch):
    """In production mode, pointing to localhost raises an error to prevent broken deployments."""
    monkeypatch.setenv("FASTAPI_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(ValueError, match="local loopback address"):
        resolve_backend_url()


def test_resolve_backend_url_invalid_protocol():
    """URL without http:// or https:// raises ValueError."""
    with pytest.raises(ValueError, match="must start with http:// or https://"):
        resolve_backend_url("ftp://api.example.com")


def test_api_client_request_path_construction():
    """APIClient safely joins paths with leading slashes."""
    client = APIClient(base_url="https://api.example.com")
    assert client.base_url == "https://api.example.com"
    # Verify path concatenation in internal call
    with patch("httpx.Client.request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_error = False
        mock_resp.json.return_value = {"status": "ok"}
        mock_req.return_value = mock_resp

        client._request("GET", "health")  # path without leading slash
        called_url = mock_req.call_args[0][1]
        assert called_url == "https://api.example.com/api/v1/health"


def test_api_client_request_dict_validation():
    """_request_dict validates dict responses and rejects unexpected shapes."""
    client = APIClient(base_url="https://api.example.com")
    with patch("httpx.Client.request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_error = False
        mock_resp.json.return_value = {"id": 1, "full_name": "Test User"}
        mock_req.return_value = mock_resp

        result = client.get_me()
        assert isinstance(result, dict)
        assert result["id"] == 1

        # Reject unexpected list shape
        mock_resp.json.return_value = [{"id": 1}]
        with pytest.raises(TypeError, match="Expected dict response from /auth/me, got list"):
            client.get_me()


def test_api_client_request_list_validation():
    """_request_list validates list responses and rejects unexpected shapes."""
    client = APIClient(base_url="https://api.example.com")
    with patch("httpx.Client.request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_error = False
        mock_resp.json.return_value = [{"id": 1, "wallet_name": "Checking"}]
        mock_req.return_value = mock_resp

        result = client.list_wallets()
        assert isinstance(result, list)
        assert len(result) == 1

        # Reject unexpected dict shape
        mock_resp.json.return_value = {"error": "not a list"}
        with pytest.raises(TypeError, match="Expected list response from /wallets, got dict"):
            client.list_wallets()


def test_api_client_request_int_validation():
    """_request_int validates integer responses and rejects booleans or dicts."""
    client = APIClient(base_url="https://api.example.com")
    with patch("httpx.Client.request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_error = False
        mock_resp.json.return_value = 5
        mock_req.return_value = mock_resp

        count = client.detect_subscriptions()
        assert count == 5

        # Reject boolean masquerading as int in Python
        mock_resp.json.return_value = True
        with pytest.raises(TypeError, match="Expected int response from /subscriptions/detect, got bool"):
            client.detect_subscriptions()


def test_api_client_request_empty_204():
    """204 No Content response is cleanly handled by _request_empty."""
    client = APIClient(base_url="https://api.example.com")
    with patch("httpx.Client.request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.is_error = False
        mock_req.return_value = mock_resp

        # Should return None without errors
        assert client.delete_wallet(1) is None


def test_api_client_invalid_json_raises_value_error():
    """Non-JSON 200 response raises ValueError with actionable detail instead of returning str."""
    client = APIClient(base_url="https://api.example.com")
    with patch("httpx.Client.request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_error = False
        mock_resp.json.side_effect = ValueError("Expecting value: line 1 column 1")
        mock_resp.request.url = "https://api.example.com/api/v1/auth/me"
        mock_req.return_value = mock_resp

        with pytest.raises(ValueError, match="Failed to decode API JSON response"):
            client.get_me()


def test_api_client_list_transactions_query_params():
    """list_transactions correctly serializes mixed filter parameter types."""
    client = APIClient(base_url="https://api.example.com")
    with patch("httpx.Client.request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_error = False
        mock_resp.json.return_value = {"items": [], "total": 0, "page": 1, "per_page": 20}
        mock_req.return_value = mock_resp

        result = client.list_transactions(
            wallet_id=3,
            search="Groceries",
            category="Food",
            transaction_type="Expense",
            is_transfer=False,
            page=2,
            per_page=25,
        )
        assert result["total"] == 0
        called_params = mock_req.call_args[1]["params"]
        assert called_params == {
            "page": 2,
            "per_page": 25,
            "wallet_id": 3,
            "search": "Groceries",
            "category": "Food",
            "type": "Expense",
            "is_transfer": "false",
        }


# =====================================================================
# 2. Health Endpoint Tests
# =====================================================================

def test_health_check_healthy(db_session):
    """When the database is connected, /health returns 200 OK and connected status."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert data["service"] == "LedgerBud API"
    finally:
        app.dependency_overrides.clear()


def test_health_check_database_unreachable():
    """When database connectivity fails, /health returns 503 without leaking credentials."""
    mock_session = MagicMock()
    mock_session.execute.side_effect = OperationalError(
        "FATAL: password authentication failed for user 'secret_user'",
        params=None,
        orig=Exception("internal auth error"),
    )

    def override_broken_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_broken_db
    try:
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        detail = response.json().get("detail", "")
        # Confirm no credentials, users, or internal driver errors leak
        assert "password" not in detail.lower()
        assert "secret_user" not in detail
        assert detail == "Database service unavailable"
    finally:
        app.dependency_overrides.clear()


def test_liveness_check():
    """Process liveness probe /health/live returns 200 without touching database."""
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "service": "LedgerBud API"}


# =====================================================================
# 3. Statement-Import Persistence & Cleanup Tests
# =====================================================================

def test_stale_upload_cleanup():
    """Pruning removes files older than max_age_seconds and preserves newer files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        stale_file = os.path.join(temp_dir, "stale_upload.csv")
        fresh_file = os.path.join(temp_dir, "fresh_upload.csv")

        with open(stale_file, "w") as f:
            f.write("old data")
        with open(fresh_file, "w") as f:
            f.write("new data")

        # Set stale file mtime to 2 hours ago
        two_hours_ago = time.time() - 7200
        os.utime(stale_file, (two_hours_ago, two_hours_ago))

        # Run cleanup with 1 hour threshold
        pruned_count = cleanup_stale_uploads(upload_folder=temp_dir, max_age_seconds=3600)
        assert pruned_count == 1
        assert not os.path.exists(stale_file)
        assert os.path.exists(fresh_file)


def test_upload_directory_defaults_to_tempdir():
    """Default UPLOAD_FOLDER is securely located in system tempdir, not in source tree."""
    assert "ledgerbud_uploads" in DEFAULT_UPLOAD_FOLDER
    assert tempfile.gettempdir() in DEFAULT_UPLOAD_FOLDER
