from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.core.config import validate_security_settings
from app.core.security import create_setup_token, verify_setup_token
from app.models import UserRole
from app.web.deps import get_current_admin
from app.web.setup_guard import require_setup_open


def test_setup_token_is_signed_scoped_and_tamper_evident():
    token = create_setup_token()

    assert verify_setup_token(token)
    assert not verify_setup_token(f"{token}tampered")
    assert not verify_setup_token(None)


@pytest.mark.asyncio
async def test_non_admin_role_is_rejected():
    request = SimpleNamespace(cookies={"admin_token": "token"})
    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(
        scalar_one_or_none=Mock(return_value=SimpleNamespace(id=7, role=UserRole.GUEST))
    )

    with patch("app.web.deps.decode_access_token", return_value={"sub": "7"}):
        with pytest.raises(HTTPException) as exc:
            await get_current_admin(request, db)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_setup_routes_are_closed_after_completion():
    with patch(
        "app.web.setup_guard.SetupStateService.is_initial_setup_done",
        new=AsyncMock(return_value=True),
    ):
        with pytest.raises(HTTPException) as exc:
            await require_setup_open()

    assert exc.value.status_code == 404


def test_production_rejects_development_secrets():
    with pytest.raises(RuntimeError):
        validate_security_settings("production", "dev_secret_key_change_me", "easycamp_secret")

    validate_security_settings("production", "strong-secret-a", "strong-secret-b")
    validate_security_settings("development", "dev_secret_key_change_me", "easycamp_secret")
