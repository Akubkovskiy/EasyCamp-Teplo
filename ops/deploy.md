# EasyCamp Deploy

## Purpose

Provide the standard deploy entrypoint for the booking bot without duplicating the deeper deployment notes.

## Canonical sources

Read first:
- `docs/DEPLOYMENT.md`
- `docker-compose.yml`
- `.env.example`

## Deploy interpretation

Deploy is stateful because it depends on:
- `easycamp.db`
- mounted logs
- Google credentials
- scheduler and sync behavior

## Pre-deploy checks

- complete `ops/release-gates.md`, including the Docker-capable build gate
- complete the ordered `ops/pre-deploy-handoff.md` for the hardening candidate
- confirm whether the change touches booking logic, scheduler behavior, or integrations
- verify rollback path for DB-sensitive changes
- treat duplicate-guard and overlap logic as business-critical
- confirm all `RESTORE_*` flags are false and `RESTORE_DRIVE_FILE_ID` is empty
  for a normal application boot

## Post-deploy checks

- `/health` is live and `/ready` confirms DB/schema readiness
- container reaches `healthy` without a restart loop
- bot responds
- startup sync does not produce duplicate or conflicting reservations
- credentials paths still resolve correctly

Database recovery is a separate maintenance deployment. Follow
`ops/restore.md`; never enable restore flags during a normal rolling restart.

## Revision `c8b1a6f4d2e9`

Before starting code that expects durable external-booking identity, follow the
snapshot and duplicate preflight in `ops/backup.md`, then run `alembic upgrade
head`. The migration fails closed when legacy `(source, external_id)` duplicates
exist. Do not bypass that check or start ingestion until the index is present.

Rollback is documented in `ops/restore.md`. No automatic production migration,
deploy, restart, or duplicate-row deletion is part of this repository change.

## Revision `f2a4c6e8b0d1`

This revision introduces inactive/archived houses. The current production
house-4 orphan graph requires the separate, fail-closed procedure in
`ops/house4-remediation.md`; `alembic upgrade head` does not silently repair or
delete business data. Do not start the candidate while any foreign-key
violation remains because `/ready` will fail and booking writers stay disabled.
