from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth_schema import (
    SignupRequest, LoginRequest, TokenResponse, UserOut, GoogleExchangeRequest, GoogleLinkRequest,
)
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.services.firebase_auth_service import verify_google_id_token
from app.services.google_user_service import (
    exchange_google_user, link_google_user, lock_email_creation, find_email_accounts, is_unique_violation,
)

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    lock_email_creation(db, str(payload.email))
    existing = find_email_accounts(db, str(payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if not is_unique_violation(exc):
            raise
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from exc
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or user.password_hash is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/auth/google/exchange", response_model=TokenResponse)
def google_exchange(payload: GoogleExchangeRequest, db: Session = Depends(get_db)):
    identity = verify_google_id_token(payload.id_token)
    user = exchange_google_user(db, identity)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/auth/google/link", response_model=TokenResponse)
def google_link(
    payload: GoogleLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    identity = verify_google_id_token(payload.id_token)
    user = link_google_user(db, current_user, identity, payload.current_password)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
