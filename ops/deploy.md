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

- confirm whether the change touches booking logic, scheduler behavior, or integrations
- verify rollback path for DB-sensitive changes
- treat duplicate-guard and overlap logic as business-critical

## Post-deploy checks

- container healthy
- bot responds
- startup sync does not produce duplicate or conflicting reservations
- credentials paths still resolve correctly

## Revision `c8b1a6f4d2e9`

Before starting code that expects durable external-booking identity, follow the
snapshot and duplicate preflight in `ops/backup.md`, then run `alembic upgrade
head`. The migration fails closed when legacy `(source, external_id)` duplicates
exist. Do not bypass that check or start ingestion until the index is present.

Rollback is documented in `ops/restore.md`. No automatic production migration,
deploy, restart, or duplicate-row deletion is part of this repository change.
