import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assistant.ask import ASSISTANT_READ_SCOPE
from app.assistant.contracts import AssistantRole
from app.assistant.session_store import (
    SessionPolicyError,
    SessionStoreError,
    SqlAlchemyTrustedSessionStore,
)
from app.database import Base
from app.models import AssistantSession, User, UserRole

NOW = datetime(2026, 9, 2, 12, tzinfo=timezone.utc)


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db:
        db.add(User(telegram_id=111, role=UserRole.OWNER, name="Owner test"))
        await db.commit()
    yield session_factory
    await engine.dispose()


def token_factory():
    counter = 0

    def next_token():
        nonlocal counter
        counter += 1
        return f"owner-session-{counter}"

    return next_token


@pytest.mark.asyncio
async def test_issue_resolve_stores_only_hashed_token_and_typed_metadata(session_factory):
    async with session_factory() as db:
        store = SqlAlchemyTrustedSessionStore(
            db,
            clock=lambda: NOW,
            token_factory=token_factory(),
        )

        issued = await store.issue(actor_telegram_id=111, actor_role=AssistantRole.OWNER)
        resolved = await store.resolve(issued.session_id)
        row = (await db.execute(select(AssistantSession))).scalar_one()

        assert resolved == issued
        assert row.session_id_hash != issued.session_id
        assert issued.session_id not in row.scopes_json
        assert json.loads(row.scopes_json) == [ASSISTANT_READ_SCOPE]
        assert row.actor_telegram_id == 111
        assert row.actor_role == AssistantRole.OWNER.value


@pytest.mark.asyncio
async def test_issue_rejects_non_owner_missing_scope_and_unsafe_ttl(session_factory):
    async with session_factory() as db:
        store = SqlAlchemyTrustedSessionStore(
            db,
            clock=lambda: NOW,
            token_factory=token_factory(),
            max_ttl_seconds=60,
        )

        with pytest.raises(SessionPolicyError):
            await store.issue(actor_telegram_id=111, actor_role=AssistantRole.ADMIN)
        with pytest.raises(SessionPolicyError):
            await store.issue(actor_telegram_id=222, actor_role=AssistantRole.OWNER)
        with pytest.raises(SessionPolicyError):
            await store.issue(
                actor_telegram_id=111,
                actor_role=AssistantRole.OWNER,
                scopes={"assistant:write"},
            )
        with pytest.raises(SessionPolicyError):
            await store.issue(
                actor_telegram_id=111,
                actor_role=AssistantRole.OWNER,
                scopes={ASSISTANT_READ_SCOPE, "assistant:write"},
            )
        with pytest.raises(SessionPolicyError):
            await store.issue(actor_telegram_id=111, actor_role=AssistantRole.OWNER, ttl_seconds=0)
        with pytest.raises(SessionPolicyError):
            await store.issue(actor_telegram_id=111, actor_role=AssistantRole.OWNER, ttl_seconds=61)
        with pytest.raises(SessionPolicyError):
            await store.issue(
                actor_telegram_id=111,
                actor_role=AssistantRole.OWNER,
                scopes=[ASSISTANT_READ_SCOPE, 1],
            )


@pytest.mark.asyncio
async def test_revoke_requires_bound_actor_and_is_idempotent(session_factory):
    async with session_factory() as db:
        store = SqlAlchemyTrustedSessionStore(
            db,
            clock=lambda: NOW,
            token_factory=token_factory(),
        )
        issued = await store.issue(actor_telegram_id=111, actor_role=AssistantRole.OWNER)

        assert await store.revoke(issued.session_id, actor_telegram_id=222) is False
        assert await store.resolve(issued.session_id) == issued
        assert (
            await store.revoke(
                issued.session_id,
                actor_telegram_id=111,
                reason="owner_logout",
            )
            is True
        )
        assert await store.resolve(issued.session_id) is None
        assert await store.revoke(issued.session_id, actor_telegram_id=111) is False

        row = (await db.execute(select(AssistantSession))).scalar_one()
        assert row.revoked_at is not None
        assert row.revoked_by_telegram_id == 111
        assert row.revocation_reason == "owner_logout"


@pytest.mark.asyncio
async def test_cleanup_removes_expired_but_keeps_revocation_metadata_until_expiry(
    session_factory,
):
    current = {"value": NOW}
    async with session_factory() as db:
        store = SqlAlchemyTrustedSessionStore(
            db,
            clock=lambda: current["value"],
            token_factory=token_factory(),
        )
        expired = await store.issue(
            actor_telegram_id=111,
            actor_role=AssistantRole.OWNER,
            ttl_seconds=10,
        )
        revoked = await store.issue(
            actor_telegram_id=111,
            actor_role=AssistantRole.OWNER,
            ttl_seconds=100,
        )
        assert await store.revoke(revoked.session_id, actor_telegram_id=111) is True

        current["value"] = NOW + timedelta(seconds=20)
        assert await store.cleanup_expired() == 1
        assert await store.resolve(expired.session_id) is None
        assert await store.resolve(revoked.session_id) is None
        assert (
            await db.scalar(
                select(AssistantSession).where(
                    AssistantSession.session_id_hash.is_not(None)
                )
            )
            is not None
        )

        current["value"] = NOW + timedelta(seconds=101)
        assert await store.cleanup_expired() == 1
        assert await db.scalar(select(AssistantSession)) is None


@pytest.mark.asyncio
async def test_malformed_persisted_session_fails_closed(session_factory):
    async with session_factory() as db:
        db.add(
            AssistantSession(
                session_id_hash=hashlib.sha256(b"malformed-session").hexdigest(),
                actor_telegram_id=111,
                actor_role="not-a-role",
                scopes_json="not-json",
                issued_at=NOW.replace(tzinfo=None),
                expires_at=(NOW + timedelta(hours=1)).replace(tzinfo=None),
                created_at=NOW.replace(tzinfo=None),
            )
        )
        await db.commit()
        store = SqlAlchemyTrustedSessionStore(db, clock=lambda: NOW)

        assert await store.resolve("malformed-session") is None


def test_naive_store_clock_fails_closed():
    with pytest.raises(SessionStoreError):
        SqlAlchemyTrustedSessionStore(
            object(),
            clock=lambda: NOW.replace(tzinfo=None),
        )._now()
