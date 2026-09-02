"""Server-side lifecycle for trusted owner assistant sessions.

The store keeps only a hash of the opaque session token. It is intentionally a
business-infrastructure component, not a model-facing database capability.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Callable, Collection
from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable

from pydantic import ValidationError
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.ask import (
    ASSISTANT_READ_SCOPE,
    TrustedSession,
    TrustedSessionResolver,
)
from app.assistant.contracts import AssistantRole
from app.models import AssistantSession, User, UserRole

DEFAULT_SESSION_TTL_SECONDS = 1800
MAX_SESSION_TTL_SECONDS = 86400
SESSION_TOKEN_BYTES = 32


class SessionStoreError(RuntimeError):
    """Infrastructure failure while issuing or persisting a session."""


class SessionPolicyError(ValueError):
    """Caller requested a session outside the owner-only policy."""


@runtime_checkable
class TrustedSessionStore(TrustedSessionResolver, Protocol):
    """Issuer, resolver and lifecycle operations required by the Telegram bridge."""

    async def issue(
        self,
        *,
        actor_telegram_id: int,
        actor_role: AssistantRole,
        scopes: Collection[str] = (ASSISTANT_READ_SCOPE,),
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> TrustedSession: ...

    async def revoke(
        self,
        session_id: str,
        *,
        actor_telegram_id: int,
        reason: str | None = None,
    ) -> bool: ...

    async def cleanup_expired(self, *, now: datetime | None = None) -> int: ...


Clock = Callable[[], datetime]
TokenFactory = Callable[[], str]


class SqlAlchemyTrustedSessionStore:
    """Persist trusted sessions without retaining raw bearer tokens."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        clock: Clock | None = None,
        token_factory: TokenFactory | None = None,
        max_ttl_seconds: int = MAX_SESSION_TTL_SECONDS,
    ) -> None:
        if max_ttl_seconds <= 0:
            raise ValueError("max_ttl_seconds must be positive")
        self._db = db
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._token_factory = token_factory or (
            lambda: secrets.token_urlsafe(SESSION_TOKEN_BYTES)
        )
        self._max_ttl_seconds = max_ttl_seconds

    async def issue(
        self,
        *,
        actor_telegram_id: int,
        actor_role: AssistantRole,
        scopes: Collection[str] = (ASSISTANT_READ_SCOPE,),
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> TrustedSession:
        role = _require_owner_role(actor_role)
        _require_telegram_id(actor_telegram_id)
        if not await self._is_current_owner(actor_telegram_id):
            raise SessionPolicyError("Telegram actor is not a current owner")
        normalized_scopes = _normalize_scopes(scopes)
        if ASSISTANT_READ_SCOPE not in normalized_scopes:
            raise SessionPolicyError("assistant:read scope is required")
        if normalized_scopes != {ASSISTANT_READ_SCOPE}:
            raise SessionPolicyError("unsupported assistant scope")
        if (
            isinstance(ttl_seconds, bool)
            or not isinstance(ttl_seconds, int)
            or ttl_seconds <= 0
            or ttl_seconds > self._max_ttl_seconds
        ):
            raise SessionPolicyError("session TTL is outside the allowed range")

        issued_at = self._now()
        expires_at = issued_at + timedelta(seconds=ttl_seconds)
        for _attempt in range(3):
            session_id = self._new_session_id()
            row = AssistantSession(
                session_id_hash=_hash_session_id(session_id),
                actor_telegram_id=actor_telegram_id,
                actor_role=role.value,
                scopes_json=json.dumps(sorted(normalized_scopes), separators=(",", ":")),
                issued_at=_storage_time(issued_at),
                expires_at=_storage_time(expires_at),
                created_at=_storage_time(issued_at),
            )
            self._db.add(row)
            try:
                await self._db.commit()
            except IntegrityError as exc:
                await self._db.rollback()
                if _attempt == 2:
                    raise SessionStoreError("could not allocate a unique session") from exc
                continue
            return TrustedSession(
                session_id=session_id,
                actor_telegram_id=actor_telegram_id,
                actor_role=role,
                scopes=normalized_scopes,
                issued_at=issued_at,
                expires_at=expires_at,
            )
        raise SessionStoreError("could not allocate a unique session")

    async def resolve(self, session_id: str) -> TrustedSession | None:
        if not _valid_session_id(session_id):
            return None
        result = await self._db.execute(
            select(AssistantSession).where(
                AssistantSession.session_id_hash == _hash_session_id(session_id)
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        now = self._now()
        issued_at = _aware_time(row.issued_at)
        expires_at = _aware_time(row.expires_at)
        if row.revoked_at is not None or issued_at > now or expires_at <= now:
            return None
        if not await self._is_current_owner(row.actor_telegram_id):
            return None
        try:
            scopes = json.loads(row.scopes_json)
            if not isinstance(scopes, list) or not all(isinstance(scope, str) for scope in scopes):
                return None
            return TrustedSession(
                session_id=session_id,
                actor_telegram_id=row.actor_telegram_id,
                actor_role=AssistantRole(row.actor_role),
                scopes=set(scopes),
                issued_at=issued_at,
                expires_at=expires_at,
            )
        except (TypeError, ValueError, ValidationError, json.JSONDecodeError):
            return None

    async def revoke(
        self,
        session_id: str,
        *,
        actor_telegram_id: int,
        reason: str | None = None,
    ) -> bool:
        if not _valid_session_id(session_id):
            return False
        _require_telegram_id(actor_telegram_id)
        safe_reason = _normalize_reason(reason)
        result = await self._db.execute(
            update(AssistantSession)
            .where(
                AssistantSession.session_id_hash == _hash_session_id(session_id),
                AssistantSession.actor_telegram_id == actor_telegram_id,
                AssistantSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=_storage_time(self._now()),
                revoked_by_telegram_id=actor_telegram_id,
                revocation_reason=safe_reason,
            )
        )
        await self._db.commit()
        return result.rowcount == 1

    async def cleanup_expired(self, *, now: datetime | None = None) -> int:
        target = self._now() if now is None else _require_aware_time(now)
        result = await self._db.execute(
            delete(AssistantSession).where(
                AssistantSession.expires_at <= _storage_time(target)
            )
        )
        await self._db.commit()
        return max(result.rowcount or 0, 0)

    def _new_session_id(self) -> str:
        session_id = self._token_factory()
        if not _valid_session_id(session_id):
            raise SessionStoreError("token factory returned an invalid session id")
        return session_id

    def _now(self) -> datetime:
        return _require_aware_time(self._clock())

    async def _is_current_owner(self, actor_telegram_id: int) -> bool:
        try:
            result = await self._db.execute(
                select(User.id).where(
                    User.telegram_id == actor_telegram_id,
                    User.role == UserRole.OWNER,
                )
            )
        except Exception as exc:
            raise SessionStoreError("could not verify owner identity") from exc
        return result.scalar_one_or_none() is not None


def _require_owner_role(role: AssistantRole) -> AssistantRole:
    try:
        normalized = AssistantRole(role)
    except (TypeError, ValueError) as exc:
        raise SessionPolicyError("unknown assistant role") from exc
    if normalized != AssistantRole.OWNER:
        raise SessionPolicyError("only owner sessions are supported")
    return normalized


def _require_telegram_id(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SessionPolicyError("telegram_id must be a positive integer")


def _normalize_scopes(scopes: Collection[str]) -> set[str]:
    if isinstance(scopes, (str, bytes)):
        raise SessionPolicyError("scopes must be a collection of strings")
    if not all(isinstance(scope, str) and scope.strip() for scope in scopes):
        raise SessionPolicyError("scopes must contain non-empty strings")
    normalized = {scope.strip() for scope in scopes}
    if not normalized or len(normalized) > 16:
        raise SessionPolicyError("invalid session scopes")
    if any(len(scope) > 80 for scope in normalized):
        raise SessionPolicyError("invalid session scope length")
    return normalized


def _normalize_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    if not isinstance(reason, str):
        raise SessionPolicyError("revocation reason must be text")
    normalized = reason.strip()
    if len(normalized) > 120:
        raise SessionPolicyError("revocation reason is too long")
    return normalized or None


def _valid_session_id(value: str) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 128


def _hash_session_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_aware_time(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise SessionStoreError("session clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def _storage_time(value: datetime) -> datetime:
    return _require_aware_time(value).replace(tzinfo=None)


def _aware_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
