# EasyCamp Restore

## Purpose

Provide the standard restore entrypoint for the booking bot.

## Restore baseline

Before restoring, identify:
- the target `easycamp.db`
- the matching `.env`
- the Google credentials source
- whether scheduler and sync should remain paused during restore validation

## Validate after restore

- container starts cleanly
- bot responds
- DB path resolves correctly
- no accidental duplicate sync or replay behavior starts immediately

## Canonical references

- `docs/DEPLOYMENT.md`
- `app/services/backup_service.py`
- `memory/projects/easycamp-teplo.md`
