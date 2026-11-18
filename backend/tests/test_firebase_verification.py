from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

from fastapi import HTTPException
import pytest

from app.services import firebase_auth_service as service


def test_admin_initializes_once_under_concurrent_requests(monkeypatch):
    monkeypatch.setattr(service.settings, "FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setattr(service.settings, "FIREBASE_SERVICE_ACCOUNT_PATH", None)
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    registry = {}
    app = Mock(project_id="test-project")

    def get_app(name):
        if name not in registry:
            raise ValueError("not initialized")
        return registry[name]

    def initialize(credential, options, name):
        assert options == {"projectId": "test-project"}
        registry[name] = app
        return app

    initialize_mock = Mock(side_effect=initialize)
    monkeypatch.setattr(service.firebase_admin, "get_app", get_app)
    monkeypatch.setattr(service.firebase_admin, "initialize_app", initialize_mock)
    adc = Mock(return_value=object())
    monkeypatch.setattr(service.credentials, "ApplicationDefault", adc)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: service.get_firebase_app(), range(8)))
    assert all(result is app for result in results)
    assert initialize_mock.call_count == adc.call_count == 1


def test_admin_uses_explicit_credential_path(monkeypatch):
    monkeypatch.setattr(service.settings, "FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setattr(service.settings, "FIREBASE_SERVICE_ACCOUNT_PATH", "outside-repo.json")
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    monkeypatch.setattr(service.firebase_admin, "get_app", Mock(side_effect=ValueError("missing")))
    certificate = Mock(return_value=object())
    monkeypatch.setattr(service.credentials, "Certificate", certificate)
    monkeypatch.setattr(service.firebase_admin, "initialize_app", Mock(return_value=Mock(project_id="test-project")))
    service.get_firebase_app()
    certificate.assert_called_once_with("outside-repo.json")


def test_missing_firebase_configuration_fails_without_initialization(monkeypatch):
    monkeypatch.setattr(service.settings, "FIREBASE_PROJECT_ID", None)
    initialize = Mock()
    monkeypatch.setattr(service.firebase_admin, "initialize_app", initialize)
    with pytest.raises(HTTPException) as error:
        service.get_firebase_app()
    assert error.value.status_code == 503
    initialize.assert_not_called()


def test_unsigned_emulator_mode_is_not_accepted(monkeypatch):
    monkeypatch.setattr(service.settings, "FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
    with pytest.raises(HTTPException) as error:
        service.get_firebase_app()
    assert error.value.status_code == 503


def test_reused_admin_app_must_match_expected_project(monkeypatch):
    monkeypatch.setattr(service.settings, "FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    monkeypatch.setattr(service.firebase_admin, "get_app", Mock(return_value=Mock(project_id="wrong-project")))
    with pytest.raises(HTTPException) as error:
        service.get_firebase_app()
    assert error.value.status_code == 503


def test_invalid_service_account_does_not_expose_path(monkeypatch):
    monkeypatch.setattr(service.settings, "FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setattr(service.settings, "FIREBASE_SERVICE_ACCOUNT_PATH", "private-location")
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    monkeypatch.setattr(service.firebase_admin, "get_app", Mock(side_effect=ValueError("missing")))
    monkeypatch.setattr(service.credentials, "Certificate", Mock(side_effect=OSError("private-location")))
    with pytest.raises(HTTPException) as error:
        service.get_firebase_app()
    assert error.value.status_code == 503
    assert "private-location" not in str(error.value.detail)
