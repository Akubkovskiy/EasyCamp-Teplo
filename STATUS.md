# EasyCamp-Teplo Status

Updated: 2026-09-03
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
DB-aware readiness gates. These changes are not deployed. The branch-local
dependency audit is clean as of commit `0c8c98f`. Before first use, complete
`ops/release-gates.md` and run the Docker-capable build/Compose gate on a host
with Docker.

The branch also contains a local-only, fail-closed remediation for the audited
production `houses.id=4` orphan graph. Production has not been changed. The
required snapshot, migration, repair, and full rollback order is documented in
`ops/house4-remediation.md`.
