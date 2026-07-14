"""Firebase Authentication Helper Utilities."""

import os
import json
import time
import httpx
import jwt
from typing import Any, Dict
import firebase_admin
from firebase_admin import credentials, auth
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from app.fastapi_app.core.config import settings
from app.fastapi_app.core.exceptions import AuthenticationError, UserAlreadyExistsError

# Global variables for caching Google public certificates
_firebase_pubkeys_cache: Dict[str, str] = {}
_firebase_pubkeys_expiry: float = 0.0


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK if enabled and not already initialized."""
    if not settings.use_firebase:
        return

    if firebase_admin._apps:
        return

    # 1. Try to load service account credentials if configured
    service_account = settings.firebase_service_account_key
    if service_account:
        if os.path.exists(service_account):
            try:
                cred = credentials.Certificate(service_account)
                firebase_admin.initialize_app(cred)
                return
            except Exception as e:
                print(f"Warning: Failed to load Firebase service account from path '{service_account}': {e}")
        else:
            # Maybe it's a raw JSON string?
            try:
                cred_dict = json.loads(service_account)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                return
            except Exception as e:
                print(f"Warning: Failed to load Firebase service account as JSON string: {e}")

    # 2. Initialize with project ID if provided
    project_id = settings.firebase_project_id
    if project_id:
        try:
            firebase_admin.initialize_app(options={"projectId": project_id})
            return
        except Exception as e:
            print(f"Warning: Failed to initialize Firebase with projectId '{project_id}': {e}")

    # 3. Fallback: Default initialization (reads GOOGLE_APPLICATION_CREDENTIALS)
    try:
        firebase_admin.initialize_app()
    except Exception as e:
        print(f"Warning: Failed default Firebase initialization: {e}")


def get_firebase_public_keys() -> Dict[str, str]:
    """Retrieve Google public certificates for manual signature verification, caching the result."""
    global _firebase_pubkeys_cache, _firebase_pubkeys_expiry
    now = time.time()
    if not _firebase_pubkeys_cache or now > _firebase_pubkeys_expiry:
        try:
            resp = httpx.get("https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com")
            if resp.status_code == 200:
                _firebase_pubkeys_cache = resp.json()
                # Cache for 1 hour
                _firebase_pubkeys_expiry = now + 3600
        except Exception as e:
            print(f"Error fetching Firebase public keys: {e}")
    return _firebase_pubkeys_cache


def verify_firebase_token_manually(token: str) -> Dict[str, Any]:
    """Manually verify a Firebase ID token JWT against Google's public certificates."""
    project_id = settings.firebase_project_id
    if not project_id:
        raise jwt.InvalidTokenError("FIREBASE_PROJECT_ID is not configured. Cannot verify token manually.")

    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise jwt.InvalidTokenError("Firebase token header missing 'kid' field.")

    pubkeys = get_firebase_public_keys()
    cert_str = pubkeys.get(kid)
    if not cert_str:
        raise jwt.InvalidTokenError(f"Firebase public key not found for kid: {kid}")

    # Convert PEM to public key object using cryptography
    cert_obj = load_pem_x509_certificate(cert_str.encode("utf-8"), default_backend())
    public_key = cert_obj.public_key()

    decoded = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=project_id,
        issuer=f"https://securetoken.google.com/{project_id}"
    )
    return decoded


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token, falling back to manual JWT verification if Admin SDK fails."""
    # Ensure Firebase is initialized
    initialize_firebase()

    # Try standard Firebase Admin verification first
    try:
        return auth.verify_id_token(token)
    except Exception as sdk_err:
        # Fall back to manual JWT parsing and signature verification
        try:
            return verify_firebase_token_manually(token)
        except Exception as manual_err:
            raise AuthenticationError(f"Token validation failed (SDK: {sdk_err}, Manual: {manual_err})") from manual_err


def firebase_sign_in(email: str, password: str) -> Dict[str, Any]:
    """Authenticate email & password via Firebase Auth REST API."""
    api_key = settings.firebase_api_key
    if not api_key:
        raise AuthenticationError("FIREBASE_API_KEY is not configured on the server.")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        resp = httpx.post(url, json=payload, timeout=10.0)
        if resp.status_code != 200:
            error_data = resp.json().get("error", {})
            error_msg = error_data.get("message", "Authentication failed")
            raise AuthenticationError(f"Firebase Login Error: {error_msg}")
        return resp.json()
    except httpx.RequestError as e:
        raise AuthenticationError(f"Failed to communicate with Firebase Auth: {e}") from e


def firebase_sign_up(email: str, password: str) -> Dict[str, Any]:
    """Register user email & password via Firebase Auth REST API."""
    api_key = settings.firebase_api_key
    if not api_key:
        raise AuthenticationError("FIREBASE_API_KEY is not configured on the server.")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        resp = httpx.post(url, json=payload, timeout=10.0)
        if resp.status_code != 200:
            error_data = resp.json().get("error", {})
            error_msg = error_data.get("message", "")
            if "EMAIL_EXISTS" in error_msg:
                raise UserAlreadyExistsError("A user with this email already exists.")
            raise AuthenticationError(f"Firebase Signup Error: {error_msg or 'Registration failed'}")
        return resp.json()
    except httpx.RequestError as e:
        raise AuthenticationError(f"Failed to communicate with Firebase Auth: {e}") from e
