"""Resolve/link verified identities without changing local ownership IDs."""

import hashlib
import time

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.services.firebase_auth_service import GoogleIdentity, auth_error

LINK_MAX_AGE_SECONDS = 300


def lock_email_creation(db: Session, email: str) -> None:
    """Serialize Google/password creations for one email on PostgreSQL.

    The unique constraints remain authoritative, including UID races across
    different emails. SQLite test databases use those constraints directly.
    """
    if db.get_bind().dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(email.strip().lower().encode()).digest()[:8], "big", signed=True)
        db.execute(select(func.pg_advisory_xact_lock(key)))


def is_unique_violation(exc: IntegrityError) -> bool:
    original = exc.orig
    return (
        getattr(original, "pgcode", None) == "23505"
        or getattr(original, "sqlstate", None) == "23505"
        or getattr(original, "sqlite_errorname", None) in {
            "SQLITE_CONSTRAINT_UNIQUE", "SQLITE_CONSTRAINT_PRIMARYKEY"
        }
    )


def find_email_accounts(db: Session, email: str) -> list[User]:
    # Detect legacy case variants, without rewriting stored emails or aliases.
    return list(db.scalars(select(User).where(func.lower(User.email) == email.lower())))


def _raise_email_conflict(accounts: list[User]) -> None:
    if len(accounts) == 1 and accounts[0].firebase_uid is None and accounts[0].password_hash is not None:
        raise auth_error(409, "google_link_required", "Sign in to your existing account before linking Google")
    raise auth_error(409, "google_identity_conflict", "This email is already associated with an account")


def exchange_google_user(db: Session, identity: GoogleIdentity) -> User:
    user = db.scalar(select(User).where(User.firebase_uid == identity.uid))
    if user is not None:
        return user

    lock_email_creation(db, identity.email)
    # A concurrent exchange/link may have completed while we waited.
    user = db.scalar(select(User).where(User.firebase_uid == identity.uid))
    if user is not None:
        return user
    accounts = find_email_accounts(db, identity.email)
    if accounts:
        _raise_email_conflict(accounts)

    user = User(name=identity.name, email=identity.email, firebase_uid=identity.uid, password_hash=None)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if not is_unique_violation(exc):
            raise
        user = db.scalar(select(User).where(User.firebase_uid == identity.uid))
        if user is not None:
            return user
        accounts = find_email_accounts(db, identity.email)
        if accounts:
            _raise_email_conflict(accounts)
        raise auth_error(409, "google_identity_conflict", "Google identity is already associated with an account") from exc
    db.refresh(user)
    return user


def link_google_user(db: Session, current_user: User, identity: GoogleIdentity, password: str) -> User:
    # Reload after taking the lock: get_current_user may have loaded an older
    # ORM object before another linking transaction committed.
    user = db.scalar(
        select(User).where(User.id == current_user.id).with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None or user.password_hash is None or not verify_password(password, user.password_hash):
        raise auth_error(401, "account_authentication_required", "Confirm your existing account password")
    age = time.time() - identity.auth_time
    if age > LINK_MAX_AGE_SECONDS or age < -60:
        raise auth_error(403, "google_reauthentication_required", "Sign in with Google again before linking")
    if user.email.strip().lower() != identity.email.lower():
        raise auth_error(403, "google_email_mismatch", "Google email must match the authenticated account")
    owner = db.scalar(select(User).where(User.firebase_uid == identity.uid))
    if (owner is not None and owner.id != user.id) or user.firebase_uid not in (None, identity.uid):
        raise auth_error(409, "google_identity_conflict", "Google identity is already associated with an account")
    user.firebase_uid = identity.uid
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if not is_unique_violation(exc):
            raise
        raise auth_error(409, "google_identity_conflict", "Google identity is already associated with an account") from exc
    db.refresh(user)
    return user
