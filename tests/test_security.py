from datetime import timedelta

import jwt

from app.core import security


def test_access_token_round_trip(monkeypatch):
    monkeypatch.setattr(security.settings, "secret_key", "test-secret-key-at-least-32-bytes")
    monkeypatch.setattr(security.settings, "algorithm", "HS256")

    token = security.create_access_token(
        {"sub": "42", "role": "admin"},
        expires_delta=timedelta(minutes=5),
    )

    payload = security.decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert isinstance(payload["exp"], int)


def test_expired_access_token_is_rejected(monkeypatch):
    monkeypatch.setattr(security.settings, "secret_key", "test-secret-key-at-least-32-bytes")
    monkeypatch.setattr(security.settings, "algorithm", "HS256")
    token = security.create_access_token(
        {"sub": "42"},
        expires_delta=timedelta(seconds=-1),
    )

    assert security.decode_access_token(token) is None


def test_access_token_with_invalid_signature_is_rejected(monkeypatch):
    monkeypatch.setattr(security.settings, "secret_key", "expected-secret-key-at-least-32-bytes")
    monkeypatch.setattr(security.settings, "algorithm", "HS256")
    token = jwt.encode(
        {"sub": "42"},
        "wrong-secret-key-at-least-32-bytes-long",
        algorithm="HS256",
    )

    assert security.decode_access_token(token) is None
