# EasyCamp-Teplo — Repo Guidance

## What This Repo Is

EasyCamp-Teplo is the Telegram booking bot for the Teplo glamping resort in Arkhyz.
It handles bookings, availability, guest communication, Avito sync, Google Sheets sync, and operational tasking for the resort workflow.

This repo is production-sensitive because it owns live reservation state and integrations that can affect real bookings.

## Read First

Before editing anything, inspect:

1. `STATUS.md`
2. `INDEX.md`
3. `README.md`
4. `docker-compose.yml`
5. `.env.example`
6. `app/services/backup_service.py`
7. `app/` entrypoints, handlers, and service code
8. `docs/DEPLOYMENT.md`
9. `docs/architecture.md`
10. `docs/google_sheets_setup.md`
11. `memory/projects/easycamp-teplo.md`

If the task touches a specific feature area, also read the matching module files under `app/`.

## Architecture Snapshot

- Python 3.11
- FastAPI + aiogram 3.x
- SQLite via SQLAlchemy async
- APScheduler for background sync
- Docker Compose deployment

The runtime shape is simple but stateful:
- one `app` container
- local SQLite database on a mounted volume
- local logs on a mounted volume
- Google credentials mounted into the container

## Deploy Shape

The current compose shape is:
- `docker compose up -d --build`
- runtime container name: `easycamp_bot`
- exposed port: `8000:8000`

The deploy is not just code deployment. It also depends on:
- `.env`
- `google-credentials.json`
- the SQLite file under `./data/`
- the current booking/state data in the mounted volume

## State And Backups

Primary state:
- `./data/easycamp.db`
- `./logs/`
- Google integration credentials
- any runtime config stored outside git

## Memory Structure

This repo uses the shared Obsidian memory model from `ai-infra`.

Primary durable notes:
- `memory/projects/easycamp-teplo.md`
- `memory/servers/fi.md`
- `memory/PROJECTS.md`

Use shared memory for:
- deployment and architecture facts
- booking-system risk notes
- operational decisions
- cross-project links with `teplo-v-arkhyze`

Do not use shared memory for:
- live booking rows
- raw sync logs
- local scheduler/runtime traces

Important local/runtime state outside Obsidian:
- `easycamp.db`
- mounted logs
- `.env`
- `google-credentials.json`

There is an existing Google Drive backup implementation in `app/services/backup_service.py`.
That makes backup logic part of the application surface, so changes there should be treated carefully.

When touching backup or restore code:
- check whether the database path logic still matches Docker and local execution
- verify credentials path handling
- make sure restore does not overwrite good live data unexpectedly

## High-Risk Areas

- SQLite schema or data migration changes
- Google credentials or Sheets/Drive integration
- Avito sync logic
- booking overlap or duplicate-guard behavior
- scheduler behavior on startup or periodic sync
- any change that can silently affect reservation state

The Avito duplicate/overlap problem is especially important:
- disputed dates should not create duplicate reservations
- temporary holds, overlap checks, and alerting behavior must be preserved
- if a change touches reservation ingestion, verify that it cannot create double-booking windows

## Safe Working Rules

- Read before editing.
- Prefer small, reviewable patches.
- Do not print secrets from `.env` or `google-credentials.json`.
- Do not assume SQLite state is disposable.
- If a change affects sync or booking logic, define the rollback path first.
- If a deploy is needed, prefer a bounded rebuild and verification over broad restarts.

## What Not To Touch Casually

- `google-credentials.json`
- the live SQLite database file
- Avito sync rules and duplicate guards
- scheduler intervals or startup sync behavior
- any code path that could retroactively alter existing bookings

## Expected Agent Behavior

When working here, first answer:
- what part of the booking pipeline is involved
- what file owns the change
- what state could be affected
- how to roll back if it goes wrong

Then make the smallest safe change.

## Structure Tier

Tier 2 service project under `infra/agent-map/PROJECT-STRUCTURE-STANDARD.md`.

This repo is stateful and business-sensitive because:
- bookings are real-world commitments
- SQLite and scheduler behavior matter
- external integrations can create duplicate or conflicting state

## Ops Surface

Use these repo-local entrypoints first:
- `STATUS.md`
- `INDEX.md`
- `ops/deploy.md`
- `ops/backup.md`
- `ops/restore.md`

Use shared notes for wider context:
- `memory/projects/easycamp-teplo.md`
- `memory/servers/fi.md`
- `memory/projects/teplo-v-arkhyze.md`
