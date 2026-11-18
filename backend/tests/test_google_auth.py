from concurrent.futures import ThreadPoolExecutor
from datetime import date
import time

from firebase_admin import auth
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, decode_access_token, hash_password
from app.models.user import User
from app.models.report import Report
from app.models.chat_history import ChatHistory


def signup(client, email="google@example.com", password=" local password "):
    response = client.post("/signup", json={"name": "Local User", "email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def exchange(client, token="firebase-token"):
    return client.post("/auth/google/exchange", json={"id_token": token})


def link(client, app_token, password=" local password ", token="firebase-token"):
    return client.post(
        "/auth/google/link", headers={"Authorization": f"Bearer {app_token}"},
        json={"id_token": token, "current_password": password},
    )


def test_valid_token_creates_google_only_user_and_application_jwt(client, sdk_verifier, db):
    response = exchange(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "user"}
    assert body["token_type"] == "bearer"
    assert set(body["user"]) == {"id", "name", "email"}
    assert isinstance(body["user"]["id"], int)
    payload = decode_access_token(body["access_token"])
    assert set(payload) == {"sub", "exp"}
    assert payload["sub"] == str(body["user"]["id"])
    user = db.get(User, body["user"]["id"])
    assert user.firebase_uid == "google-uid-1"
    assert user.password_hash is None
    assert sdk_verifier.call_args.kwargs["check_revoked"] is True
    me = client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json() == body["user"]
    assert client.get("/me", headers={"Authorization": "Bearer firebase-token"}).status_code == 401


def test_existing_linked_user_login_preserves_local_profile(client, claims, db):
    first = exchange(client).json()
    claims.update(email="changed@example.com", name="Changed Google Name")
    second = exchange(client)
    assert second.status_code == 200
    assert second.json()["user"] == first["user"]
    assert db.scalar(select(func.count()).select_from(User)) == 1


@pytest.mark.parametrize(("failure", "code"), [
    (auth.InvalidIdTokenError("invalid"), "firebase_token_invalid"),
    (auth.ExpiredIdTokenError("expired", None), "firebase_token_expired"),
    (auth.RevokedIdTokenError("revoked"), "firebase_token_revoked"),
    (auth.UserDisabledError("disabled"), "firebase_user_unavailable"),
    (auth.UserNotFoundError("deleted"), "firebase_user_unavailable"),
])
def test_invalid_expired_revoked_and_unavailable_identities(client, sdk_verifier, db, failure, code):
    sdk_verifier.side_effect = failure
    response = exchange(client)
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == code
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_certificate_fetch_failure_is_service_error(client, sdk_verifier):
    sdk_verifier.side_effect = auth.CertificateFetchError("unavailable", None)
    assert exchange(client).status_code == 503


@pytest.mark.parametrize(("change", "code"), [
    ({"email_verified": False}, "google_email_unverified"),
    ({"email_verified": "true"}, "google_email_unverified"),
    ({"firebase": {"sign_in_provider": "password"}}, "google_provider_required"),
    ({"email": "not-an-email"}, "google_email_invalid"),
])
def test_rejects_unverified_non_google_and_invalid_email(client, claims, change, code):
    claims.update(change)
    response = exchange(client)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == code


def test_existing_password_email_is_not_automatically_linked(client, db):
    local = signup(client)
    response = exchange(client)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "google_link_required"
    assert "access_token" not in response.json()
    user = db.get(User, local["user"]["id"])
    assert user.firebase_uid is None
    assert user.password_hash is not None
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_authenticated_link_preserves_id_hash_reports_and_chat_history(client, db):
    local = signup(client)
    user = db.get(User, local["user"]["id"])
    old_hash = user.password_hash
    report = Report(user_id=user.id, report_name="existing.pdf", report_date=date.today(), file_url="existing.pdf")
    db.add(report)
    db.commit()
    history = ChatHistory(user_id=user.id, report_id=report.id, question="Old question", answer="Old answer")
    db.add(history)
    db.commit()
    report_id, history_id = report.id, history.id

    # Authenticate through the existing login endpoint before linking.
    login = client.post("/login", json={"email": user.email, "password": " local password "})
    assert login.status_code == 200
    response = link(client, login.json()["access_token"])
    assert response.status_code == 200
    assert response.json()["user"] == local["user"]
    db.expire_all()
    assert db.get(User, user.id).password_hash == old_hash
    assert db.get(User, user.id).firebase_uid == "google-uid-1"
    assert db.get(Report, report_id).user_id == user.id
    assert db.get(ChatHistory, history_id).user_id == user.id
    assert exchange(client).json()["user"]["id"] == user.id
    assert link(client, login.json()["access_token"]).status_code == 200
    assert client.post("/login", json={"email": user.email, "password": " local password "}).status_code == 200


def test_link_requires_application_authentication(client):
    signup(client)
    body = {"id_token": "firebase-token", "current_password": " local password "}
    assert client.post("/auth/google/link", json=body).status_code == 401
    assert link(client, "firebase-token").status_code == 401


def test_link_requires_password_confirmation(client, db):
    local = signup(client)
    assert link(client, local["access_token"], password="wrong").status_code == 401
    assert db.get(User, local["user"]["id"]).firebase_uid is None


def test_link_cannot_target_a_different_authenticated_email(client, db):
    local = signup(client, email="other@example.com")
    assert link(client, local["access_token"]).status_code == 403
    assert db.get(User, local["user"]["id"]).firebase_uid is None


def test_link_requires_recent_google_authentication(client, claims):
    local = signup(client)
    claims["auth_time"] = int(time.time()) - 600
    response = link(client, local["access_token"])
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "google_reauthentication_required"


def test_duplicate_uid_cannot_be_linked_to_another_account(client, db):
    first = signup(client)
    assert link(client, first["access_token"]).status_code == 200
    # Simulate historical email-case variants; never create them automatically.
    second = User(name="Legacy", email="Google@example.com", password_hash=hash_password(" local password "))
    db.add(second)
    db.commit()
    response = link(client, create_access_token({"sub": str(second.id)}))
    assert response.status_code == 409
    db.refresh(second)
    assert second.firebase_uid is None


def test_link_does_not_replace_an_existing_uid(client, claims, db):
    local = signup(client)
    assert link(client, local["access_token"]).status_code == 200
    claims["uid"] = "different-google-uid"
    assert link(client, local["access_token"]).status_code == 409
    assert db.get(User, local["user"]["id"]).firebase_uid == "google-uid-1"


def test_database_prevents_duplicate_non_null_uid_but_allows_password_accounts(client, db):
    signup(client, email="one@example.com")
    signup(client, email="two@example.com")
    db.add(User(name="Google", email="three@example.com", firebase_uid="same-uid"))
    db.commit()
    db.add(User(name="Duplicate", email="four@example.com", firebase_uid="same-uid"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.scalar(select(func.count()).select_from(User)) == 3


def test_account_must_have_at_least_one_authentication_method(db):
    db.add(User(name="No credentials", email="missing@example.com"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_existing_password_authentication_and_duplicate_signup(client):
    local = signup(client)
    login = client.post("/login", json={"email": "google@example.com", "password": " local password "})
    assert login.status_code == 200 and login.json()["user"] == local["user"]
    assert client.post("/login", json={"email": "google@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/signup", json={"name": "Duplicate", "email": "google@example.com", "password": "password"}).status_code == 400


def test_password_login_on_google_only_user_fails_cleanly(client):
    exchange(client)
    assert client.post("/login", json={"email": "google@example.com", "password": "anything"}).status_code == 401


def test_signup_cannot_duplicate_google_account_by_email_case(client):
    exchange(client)
    response = client.post("/signup", json={"name": "Duplicate", "email": "Google@example.com", "password": "password"})
    assert response.status_code == 400


def test_exchange_detects_ambiguous_legacy_email_case(client, db):
    db.add_all([
        User(name="First", email="Google@example.com", password_hash=hash_password("password")),
        User(name="Second", email="google@example.com", password_hash=hash_password("password")),
    ])
    db.commit()
    assert exchange(client).status_code == 409
    assert db.scalar(select(func.count()).select_from(User)) == 2


@pytest.mark.parametrize("endpoint", ["/auth/google/exchange", "/auth/google/link"])
def test_frontend_identity_fields_are_rejected(client, endpoint):
    local = signup(client)
    body = {"id_token": "firebase-token", "email": "forged@example.com", "user_id": 999}
    if endpoint.endswith("link"):
        body["current_password"] = " local password "
    response = client.post(endpoint, json=body, headers={"Authorization": f"Bearer {local['access_token']}"})
    assert response.status_code == 422


def _require_pg(db_engine):
    if db_engine.dialect.name != "postgresql":
        pytest.skip("Concurrent transaction checks require PostgreSQL")


def test_concurrent_google_creations_return_one_account(client, db_engine, db):
    _require_pg(db_engine)
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: exchange(client), range(4)))
    assert all(response.status_code == 200 for response in responses)
    assert len({response.json()["user"]["id"] for response in responses}) == 1
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_concurrent_google_and_password_creation(client, db_engine, db):
    _require_pg(db_engine)
    with ThreadPoolExecutor(max_workers=2) as pool:
        google = pool.submit(exchange, client)
        password = pool.submit(client.post, "/signup", json={"name": "Local", "email": "Google@example.com", "password": "password"})
        responses = [google.result(), password.result()]
    assert sorted(response.status_code for response in responses) in ([200, 400], [200, 409])
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_concurrent_links_cannot_overwrite_uid(client, claims, sdk_verifier, db_engine, db):
    _require_pg(db_engine)
    local = signup(client)
    first, second = dict(claims), {**claims, "uid": "second-uid"}
    sdk_verifier.side_effect = lambda token, **_: first if token == "first" else second
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda token: link(client, local["access_token"], token=token), ["first", "second"]))
    assert sorted(response.status_code for response in responses) == [200, 409]
    assert db.get(User, local["user"]["id"]).firebase_uid in {"google-uid-1", "second-uid"}
