# EasyCamp-Teplo Status

Updated: 2026-04-08
Tier: Tier 2
Runs on: `FI-RZ-4`

## What This Repo Owns

- booking bot behavior
- reservation state
- scheduler-driven sync tasks
- Google integrations
- SQLite-backed operational data

## Runtime Shape

- app code under `app/`
- Alembic migrations under `alembic/`
- Docker runtime through `docker-compose.yml`
- database file and logs on mounted local storage

## Production-Sensitive State

- `easycamp.db`
- `.env`
- `google-credentials.json`
- logs and scheduler state

## High-Risk Zones

- reservation ingestion / overlap checks
- scheduler startup behavior
- Google Sheets / Drive integration
- backup / restore logic

## Current Working Rule

Enter through `STATUS.md` and `INDEX.md`, then only read the booking pipeline slice involved in the task.

## Branch-only release readiness

The current Codex branch adds booking-integrity, safe SQLite recovery, CI, and
DB-aware readiness gates. These changes are not deployed. Before first use,
complete `ops/release-gates.md`, resolve the dependency-audit findings, and run
the Docker-capable build/Compose gate on a host with Docker.
