"""Verify Google identity; application sessions still use our own JWTs."""

from dataclasses import dataclass
import os
from threading import Lock

import firebase_admin
from firebase_admin import auth, credentials, exceptions
from google.auth.exceptions import GoogleAuthError
from fastapi import HTTPException
from pydantic import EmailStr, TypeAdapter, ValidationError
from requests.exceptions import RequestException

from app.core.config import settings

_APP_NAME = "google-identity"
_app_lock = Lock()
_email_adapter = TypeAdapter(EmailStr)


@dataclass(frozen=True)
class GoogleIdentity:
    uid: str
    email: str
    name: str
    auth_time: int


def auth_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code, detail={"code": code, "message": message})


def get_firebase_app() -> firebase_admin.App:
    project_id = (settings.FIREBASE_PROJECT_ID or "").strip()
    if not project_id or os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
        # The emulator accepts unsigned tokens. This production verifier must
        # never silently switch to that behavior; tests mock verification.
        raise auth_error(503, "google_auth_unavailable", "Google authentication is not configured")
    try:
        with _app_lock:
            try:
                app = firebase_admin.get_app(_APP_NAME)
            except ValueError:
                path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
                credential = credentials.Certificate(path) if path else credentials.ApplicationDefault()
                app = firebase_admin.initialize_app(
                    credential, options={"projectId": project_id}, name=_APP_NAME
                )
            if app.project_id != project_id:
                raise ValueError("Firebase project configuration changed")
            return app
    except (ValueError, OSError, GoogleAuthError) as exc:
        raise auth_error(503, "google_auth_unavailable", "Google authentication is unavailable") from exc


def verify_google_id_token(id_token: str) -> GoogleIdentity:
    app = get_firebase_app()
    try:
        claims = auth.verify_id_token(id_token, app=app, check_revoked=True)
    except auth.ExpiredIdTokenError as exc:
        raise auth_error(401, "firebase_token_expired", "Google sign-in expired; sign in again") from exc
    except auth.RevokedIdTokenError as exc:
        raise auth_error(401, "firebase_token_revoked", "Google sign-in was revoked; sign in again") from exc
    except (auth.UserDisabledError, auth.UserNotFoundError) as exc:
        raise auth_error(401, "firebase_user_unavailable", "This Google identity is unavailable") from exc
    except (auth.InvalidIdTokenError, ValueError) as exc:
        raise auth_error(401, "firebase_token_invalid", "Invalid Google sign-in token") from exc
    except (exceptions.FirebaseError, GoogleAuthError, RequestException) as exc:
        raise auth_error(503, "google_auth_unavailable", "Google authentication is unavailable") from exc

    provider = claims.get("firebase")
    if not isinstance(provider, dict) or provider.get("sign_in_provider") != "google.com":
        raise auth_error(403, "google_provider_required", "A Google sign-in token is required")
    if claims.get("email_verified") is not True:
        raise auth_error(403, "google_email_unverified", "Google email must be verified")
    uid = claims.get("uid")
    auth_time = claims.get("auth_time")
    if not isinstance(uid, str) or not 1 <= len(uid) <= 128 or type(auth_time) is not int:
        raise auth_error(401, "firebase_token_invalid", "Invalid Google identity claims")
    try:
        email = str(_email_adapter.validate_python(claims.get("email")))
    except ValidationError as exc:
        raise auth_error(403, "google_email_invalid", "A valid Google email is required") from exc
    if len(email) > 255:
        raise auth_error(403, "google_email_invalid", "A valid Google email is required")
    name = claims.get("name")
    name = name.strip()[:100] if isinstance(name, str) else ""
    return GoogleIdentity(uid=uid, email=email, name=name or "Google user", auth_time=auth_time)
