"""Firebase Authentication Helper Utilities."""

import os
import json
from typing import Any, Dict
import firebase_admin
from firebase_admin import credentials, auth

from app.fastapi_app.core.config import settings
from app.fastapi_app.core.exceptions import AuthenticationError

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

def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token using the Admin SDK."""
    # Ensure Firebase is initialized
    initialize_firebase()

    try:
        return auth.verify_id_token(token)
    except Exception as sdk_err:
        raise AuthenticationError(f"Token validation failed (SDK: {sdk_err})") from sdk_err



