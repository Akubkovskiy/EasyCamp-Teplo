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

The model must never receive an `AsyncSession`, SQLAlchemy object, database
path or raw query capability. A future wiring module may build a boundary over
those services, but it must remain outside the model/tool planner layer.

Before enabling a runtime, complete all gates in the sibling
`teplo-assistant/VERIFICATION.md`, add a server-side Telegram role/scope
resolver, supply a deployment secret for cursor signing, and run owner-only
UAT. Do not add create/update/cancel/delete/payment tools to this package until
the persistent draft, confirmation, idempotency and rollback phase is approved.
