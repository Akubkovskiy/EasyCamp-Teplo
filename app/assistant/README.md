# Assistant read-only foundation

This package is an isolated adapter for the future Teplo AI assistant. It is
not imported by `app/main.py`, has no Telegram handler, and is disabled by
default (`AssistantReadOnlyGateway(..., enabled=False)`). Importing it does not
open a database connection or call an external service.

The canonical wire contract lives in the sibling project at
`../teplo-assistant/contracts/read_only_v1.schema.json`. The local Python DTOs
in `contracts.py` mirror that v1 contract. The gateway accepts a `ReadBoundary`
dependency that must delegate to existing EasyCamp business services:

- `HouseService` for the catalog;
- `PricingService` for nightly prices and stay totals;
- `BookingService` for availability and booking reads.

`EasyCampBusinessReadBoundary` is the concrete composition adapter. It is not
wired into `app/main.py`; a future runtime must instantiate it only behind an
owner-only feature flag and pass it to the disabled-by-default
`AssistantReadOnlyGateway`.

`AssistantAskTransport` is the internal structured `/ask` handler. It is not a
FastAPI route and is not registered with Telegram or `app/main.py`. It accepts
only `session_id + intent + arguments`, requires a trusted owner context and a
server-side session verifier when enabled, and forwards only the six v1
read-only intents. It has no natural-language planner and exposes no write
operation.

`TelegramTrustedAskAdapter` is the next integration boundary for a future
Telegram handler. The handler must create `TelegramActor` from the aiogram
update and pass a `TrustedSessionResolver` backed by a server-side session
store. The resolver must return a `TrustedSession` containing the same
Telegram ID, an unexpired timezone-aware lifetime, the `assistant:read` scope,
and the `owner` role. The adapter rejects disabled, unknown, expired, malformed,
unbound, out-of-scope and non-owner sessions before calling the gateway. A
session-store failure is returned as a retryable upstream error.

The current Telegram role cache and the web `admin_token` JWT are not assistant
session stores: the former has no session lifetime and the latter does not bind
to a Telegram ID. Do not wire either one into this adapter as a shortcut. Add a
real server-side session issuer/store first, then add a narrow owner-only
Telegram handler behind an explicit feature flag. Keep guest routing and all
write tools out of this boundary until the confirmation and idempotency phase
is approved.

`SqlAlchemyTrustedSessionStore` is the concrete lifecycle implementation. It
issues opaque random tokens, stores only their SHA-256 hashes, binds each
session to one current `UserRole.OWNER` Telegram ID, and records role, scopes, issue/expiry and
revocation metadata. `revoke` requires the bound actor ID; `cleanup_expired`
removes expired rows while leaving revoked-but-not-yet-expired metadata for
audit. Its database table is added by the Alembic revision
`b2c3d4e5f6a7_add_assistant_sessions.py`; applying that migration is a separate
production operation and is not performed by this change.

`build_owner_assistant_router` creates exactly one `/ask` command handler only
when its explicit `enabled=True` argument is supplied. The command accepts
JSON structured queries only, passes `message.from_user.id` as `TelegramActor`,
and has no booking write commands or natural-language planner. It returns
`None` when disabled, and `app/main.py` does not call it. The configuration
flag `ASSISTANT_TELEGRAM_ENABLED` defaults to `false` and is rejected in
production until this boundary has passed owner-only UAT.

The model must never receive an `AsyncSession`, SQLAlchemy object, database
path or raw query capability. A future wiring module may build a boundary over
those services, but it must remain outside the model/tool planner layer.

Before enabling a runtime, complete all gates in the sibling
`teplo-assistant/VERIFICATION.md`, add a server-side Telegram role/scope
resolver, supply a deployment secret for cursor signing, and run owner-only
UAT. Do not add create/update/cancel/delete/payment tools to this package until
the persistent draft, confirmation, idempotency and rollback phase is approved.
