"""
Firebase Authentication
========================
Verifies Firebase ID tokens on protected endpoints.
Set FIREBASE_PROJECT_ID env var to enable.
If not set, all requests pass through (local dev mode).
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


_firebase_admin = None
_firebase_auth_module = None
_firebase_app = None
_FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "").strip()


def _init_firebase() -> bool:
    """Lazily initialise Firebase Admin SDK."""
    global _firebase_admin, _firebase_auth_module, _firebase_app

    if _firebase_app is not None:
        return True

    if not _FIREBASE_PROJECT_ID:
        return False

    try:
        _firebase_admin = import_module("firebase_admin")
        _firebase_auth_module = import_module("firebase_admin.auth")
        credentials_mod = import_module("firebase_admin.credentials")

        # Use Application Default Credentials (works on Cloud Run automatically)
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        if cred_path:
            cred = credentials_mod.Certificate(cred_path)
        else:
            cred = credentials_mod.ApplicationDefault()

        try:
            _firebase_app = _firebase_admin.get_app()
        except Exception:
            _firebase_app = _firebase_admin.initialize_app(cred)

        return True
    except Exception:
        return False


_bearer = HTTPBearer(auto_error=False)


def verify_firebase_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency — verifies Firebase ID token.

    Modes:
    - FIREBASE_PROJECT_ID not set → dev bypass (all requests pass, uid='dev-user')
    - FIREBASE_PROJECT_ID set, token missing → 401
    - FIREBASE_PROJECT_ID set, token invalid → 403
    - FIREBASE_PROJECT_ID set, token valid → returns decoded token dict
    """
    if not _FIREBASE_PROJECT_ID:
        # Local development: bypass auth
        return {"uid": "dev-user", "email": "dev@localhost", "firebase_auth": False}

    if not _init_firebase():
        raise HTTPException(
            status_code=503,
            detail="Firebase Auth not available. Check FIREBASE_PROJECT_ID and credentials.",
        )

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Expected: 'Bearer <firebase_id_token>'",
        )

    token = credentials.credentials
    try:
        decoded = _firebase_auth_module.verify_id_token(
            token,
            check_revoked=True,
        )
        return {**decoded, "firebase_auth": True}
    except Exception as exc:
        error_msg = str(exc)
        if "expired" in error_msg.lower():
            raise HTTPException(status_code=401, detail="Firebase token expired. Please re-authenticate.")
        raise HTTPException(status_code=403, detail=f"Invalid Firebase token: {error_msg}")


def get_firebase_status() -> dict:
    """Return Firebase Auth configuration status (for health checks)."""
    return {
        "firebase_auth_enabled": bool(_FIREBASE_PROJECT_ID),
        "firebase_project_id": _FIREBASE_PROJECT_ID or "not_configured",
        "firebase_admin_available": _init_firebase() if _FIREBASE_PROJECT_ID else False,
        "mode": "production" if _FIREBASE_PROJECT_ID else "dev_bypass",
    }
