import os
import time
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Always isolate application settings from real deployment credentials. The
# separate TEST_POSTGRES_URL is used only for disposable test schemas below.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-application-secret-not-for-deployment"
os.environ["GEMINI_API_KEY"] = "test-only-unused-key"

from app.api import auth_routes
from app.db.session import Base, get_db
from app.services import firebase_auth_service


@pytest.fixture
def empty_pg_engine():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set TEST_POSTGRES_URL to a disposable PostgreSQL database")
    control = create_engine(url)
    schema = "firebase_test_" + uuid.uuid4().hex
    with control.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        yield engine
    finally:
        engine.dispose()
        with control.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()


@pytest.fixture
def db_engine(request):
    if os.environ.get("TEST_POSTGRES_URL"):
        engine = request.getfixturevalue("empty_pg_engine")
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def claims():
    return {
        "uid": "google-uid-1",
        "email": "google@example.com",
        "email_verified": True,
        "name": "Google User",
        "auth_time": int(time.time()),
        "firebase": {"sign_in_provider": "google.com"},
    }


@pytest.fixture
def sdk_verifier(monkeypatch, claims):
    from unittest.mock import Mock

    app = object()
    monkeypatch.setattr(firebase_auth_service, "get_firebase_app", lambda: app)
    verifier = Mock(return_value=claims)
    monkeypatch.setattr(firebase_auth_service.auth, "verify_id_token", verifier)
    return verifier


@pytest.fixture
def client(db_engine, sdk_verifier):
    app = FastAPI()
    app.include_router(auth_routes.router)

    def test_db():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as test_client:
        yield test_client
