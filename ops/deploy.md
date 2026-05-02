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
