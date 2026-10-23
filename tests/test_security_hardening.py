"""Regression and security hardening tests.

Covers:
1. Cross-user wallet isolation during statement upload.
2. Cross-user wallet isolation during statement commit (preventing BOLA/IDOR).
3. Legitimate statement upload and commit by the authorized wallet owner.
4. Rejection of oversized file uploads (> MAX_UPLOAD_SIZE_MB) with HTTP 413.
5. Rejection of unsupported file types and empty files with HTTP 400.
6. Cookie security attributes (Secure flag on HTTPS/production, SameSite, Max-Age).
7. CORS origin hardening (blocking wildcards with credentials, trailing slash normalization).
"""

import io
import os
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.fastapi_app.api.deps import get_current_user, get_db
from app.fastapi_app.core.config import Settings, settings
from app.fastapi_app.main import app
from app.fastapi_app.models.import_job import ImportJob
from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.models.user import User
from app.fastapi_app.models.wallet import Wallet
from app.fastapi_app.services.import_service import ImportService
from ui.auth import get_clear_cookie_script, get_set_cookie_script, is_cookie_secure


SAMPLE_CSV = b"""date,description,amount
2026-07-01,Supermarket Groceries,120.50
2026-07-02,Coffee Shop,15.00
"""


@pytest.fixture
def users_and_wallets(db_session):
    """Seed two distinct users and their respective wallets."""
    user_a = db_session.scalar(select(User).where(User.email == "test@example.com"))
    if not user_a:
        user_a = User(
            full_name="User A",
            email="usera@example.com",
            password_hash="fakehash",
            is_active=True,
        )
        db_session.add(user_a)
        db_session.commit()
        db_session.refresh(user_a)

    user_b = User(
        full_name="User B",
        email="userb@example.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    wallet_a = Wallet(
        user_id=user_a.id,
        wallet_name="User A Checking",
        wallet_type="bank",
        balance=1000.0,
        is_archived=False,
    )
    wallet_b = Wallet(
        user_id=user_b.id,
        wallet_name="User B Savings",
        wallet_type="bank",
        balance=5000.0,
        is_archived=False,
    )
    db_session.add_all([wallet_a, wallet_b])
    db_session.commit()
    db_session.refresh(wallet_a)
    db_session.refresh(wallet_b)

    return {"user_a": user_a, "user_b": user_b, "wallet_a": wallet_a, "wallet_b": wallet_b}


@pytest.fixture
def api_client(db_session):
    """Create a test client wired to the in-memory database."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# =====================================================================
# Task A Tests: Wallet Authorization in Statement Imports
# =====================================================================

def test_user_a_cannot_upload_to_user_b_wallet(api_client, users_and_wallets):
    """User A cannot upload a statement into User B's wallet (IDOR prevention)."""
    user_a = users_and_wallets["user_a"]
    wallet_b = users_and_wallets["wallet_b"]

    app.dependency_overrides[get_current_user] = lambda: user_a

    response = api_client.post(
        "/api/v1/imports/upload",
        data={"wallet_id": wallet_b.id},
        files={"file": ("statement.csv", io.BytesIO(SAMPLE_CSV), "text/csv")},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "wallet not found" in response.json()["detail"].lower()


def test_user_a_cannot_commit_import_against_user_b_wallet(api_client, users_and_wallets, db_session):
    """User A cannot commit a previously created import job owned by User B."""
    user_a = users_and_wallets["user_a"]
    user_b = users_and_wallets["user_b"]
    wallet_b = users_and_wallets["wallet_b"]

    # Create an import job directly owned by User B
    job_b = ImportJob(
        user_id=user_b.id,
        wallet_id=wallet_b.id,
        filename="nonexistent.csv",
        original_filename="userb_statement.csv",
        file_type="csv",
        status="preview",
    )
    db_session.add(job_b)
    db_session.commit()
    db_session.refresh(job_b)

    # User A attempts to commit User B's job
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = api_client.post(f"/api/v1/imports/{job_b.id}/commit")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_user_cannot_commit_with_tampered_wallet_id(db_session, users_and_wallets):
    """Even if an import job has tampered wallet_id pointing to another user's wallet, commit fails."""
    user_a = users_and_wallets["user_a"]
    wallet_b = users_and_wallets["wallet_b"]

    # Job belongs to User A, but references User B's wallet
    tampered_job = ImportJob(
        user_id=user_a.id,
        wallet_id=wallet_b.id,
        filename="tampered.csv",
        original_filename="tampered.csv",
        file_type="csv",
        status="preview",
    )
    db_session.add(tampered_job)
    db_session.commit()
    db_session.refresh(tampered_job)

    service = ImportService(db_session)
    with pytest.raises(ValueError, match="Wallet not found for this user"):
        service.commit_import(user_id=user_a.id, job_id=tampered_job.id)


def test_valid_owner_can_complete_import_workflow(api_client, users_and_wallets, db_session):
    """Authorized wallet owner can upload a statement, inspect preview, and commit transactions."""
    user_a = users_and_wallets["user_a"]
    wallet_a = users_and_wallets["wallet_a"]

    app.dependency_overrides[get_current_user] = lambda: user_a

    # 1. Upload statement
    upload_resp = api_client.post(
        "/api/v1/imports/upload",
        data={"wallet_id": wallet_a.id},
        files={"file": ("statement.csv", io.BytesIO(SAMPLE_CSV), "text/csv")},
    )
    assert upload_resp.status_code == status.HTTP_200_OK
    preview_data = upload_resp.json()
    job_id = preview_data["job_id"]
    assert preview_data["status"] == "preview"
    assert len(preview_data["transactions"]) == 2

    # 2. Commit import
    commit_resp = api_client.post(f"/api/v1/imports/{job_id}/commit")
    assert commit_resp.status_code == status.HTTP_200_OK
    commit_data = commit_resp.json()
    assert commit_data["status"] == "completed"
    assert commit_data["imported_count"] == 2

    # Verify transactions in database belong to User A and Wallet A
    txns = db_session.scalars(
        select(Transaction).where(Transaction.user_id == user_a.id, Transaction.wallet_id == wallet_a.id)
    ).all()
    assert len(txns) == 2


# =====================================================================
# Task B Tests: Upload Limits and Validation
# =====================================================================

def test_oversized_upload_rejected_at_route(api_client, users_and_wallets):
    """Uploads exceeding max_upload_size_bytes are rejected with HTTP 413 without reading unbounded bytes."""
    user_a = users_and_wallets["user_a"]
    wallet_a = users_and_wallets["wallet_a"]

    app.dependency_overrides[get_current_user] = lambda: user_a

    # Temporarily set max_upload_size_mb to 1 MB for testing
    original_mb = settings.max_upload_size_mb
    settings.max_upload_size_mb = 1

    try:
        # Create a payload slightly larger than 1 MB (1 MB + 10 KB)
        large_payload = b"date,description,amount\n" + (b"2026-07-01,Large Item,10.0\n" * 40000)
        assert len(large_payload) > settings.max_upload_size_bytes

        response = api_client.post(
            "/api/v1/imports/upload",
            data={"wallet_id": wallet_a.id},
            files={"file": ("large.csv", io.BytesIO(large_payload), "text/csv")},
        )
        assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        assert "exceeds maximum allowed size" in response.json()["detail"].lower()
    finally:
        settings.max_upload_size_mb = original_mb


def test_unsupported_file_types_rejected(api_client, users_and_wallets):
    """Files with non-whitelisted extensions are rejected with HTTP 400."""
    user_a = users_and_wallets["user_a"]
    wallet_a = users_and_wallets["wallet_a"]

    app.dependency_overrides[get_current_user] = lambda: user_a

    for bad_name in ["malware.exe", "statement.txt", "script.sh", "payload.json"]:
        response = api_client.post(
            "/api/v1/imports/upload",
            data={"wallet_id": wallet_a.id},
            files={"file": (bad_name, io.BytesIO(b"content"), "application/octet-stream")},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unsupported file type" in response.json()["detail"].lower()


def test_empty_file_rejected(api_client, users_and_wallets):
    """Empty files (0 bytes) are rejected cleanly with HTTP 400."""
    user_a = users_and_wallets["user_a"]
    wallet_a = users_and_wallets["wallet_a"]

    app.dependency_overrides[get_current_user] = lambda: user_a

    response = api_client.post(
        "/api/v1/imports/upload",
        data={"wallet_id": wallet_a.id},
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"].lower()


# =====================================================================
# Task C Tests: Authentication Cookies and CORS Configuration
# =====================================================================

def test_cookie_secure_flag_behavior(monkeypatch):
    """Cookie Secure flag is enabled in production and over HTTPS, but safely omitted in local HTTP dev."""
    # 1. Default local dev: should NOT force Secure flag unconditionally
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    assert is_cookie_secure() is False
    dev_script = get_set_cookie_script("sample_token")
    assert "lb_session_token=sample_token" in dev_script
    assert "SameSite=Lax" in dev_script
    assert "max-age=604800" in dev_script
    assert "isHttps" in dev_script

    # 2. Production environment: force_secure becomes true
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert is_cookie_secure() is True
    prod_script = get_set_cookie_script("sample_token")
    assert "true" in prod_script  # force_secure evaluated to true

    # 3. Explicit COOKIE_SECURE override
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    assert is_cookie_secure() is True

    monkeypatch.setenv("COOKIE_SECURE", "false")
    assert is_cookie_secure() is False


def test_cookie_clear_script_behavior():
    """Clear cookie script sets max-age=0 with matching SameSite and path."""
    clear_script = get_clear_cookie_script()
    assert "lb_session_token=" in clear_script
    assert "max-age=0" in clear_script
    assert "SameSite=Lax" in clear_script
    assert "path=/" in clear_script


def test_cors_rejects_wildcard_with_credentials():
    """CORS configuration must reject wildcard '*' when credentials are supported."""
    with pytest.raises(ValueError, match="Wildcard '\\*' origin is not permitted"):
        Settings(cors_origins="*")

    with pytest.raises(ValueError, match="Wildcard '\\*' origin is not permitted"):
        Settings(cors_origins=["http://localhost:3000", "*"])


def test_cors_normalizes_trailing_slashes():
    """Trailing slashes on origins are stripped to ensure exact origin matching."""
    s = Settings(cors_origins="http://localhost:3000/, https://app.ledgerbud.com/")
    assert s.cors_origins == ["http://localhost:3000", "https://app.ledgerbud.com"]


def test_cors_runtime_middleware(api_client):
    """FastAPI CORS middleware allows configured origins and denies untrusted origins."""
    # Allowed origin: http://localhost:8501
    allowed_resp = api_client.get(
        "/",
        headers={"Origin": "http://localhost:8501"},
    )
    assert allowed_resp.headers.get("access-control-allow-origin") == "http://localhost:8501"
    assert allowed_resp.headers.get("access-control-allow-credentials") == "true"

    # Untrusted origin: https://attacker.example.com
    untrusted_resp = api_client.get(
        "/",
        headers={"Origin": "https://attacker.example.com"},
    )
    assert "access-control-allow-origin" not in untrusted_resp.headers
