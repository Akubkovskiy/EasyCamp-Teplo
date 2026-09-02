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

## Rollback for revision `c8b1a6f4d2e9`

This revision only adds the unique index
`uq_bookings_source_external_id`; it does not rewrite booking rows.

1. Pause application writers and ingestion jobs.
2. Run `alembic downgrade a1b2c3d4e5f6` against the intended SQLite file.
3. Verify the index is absent with `PRAGMA index_list('bookings');`.
4. Return to the previous application revision and run a read-only booking/health canary.

If a verified pre-migration snapshot must be restored instead, keep ingestion
paused, restore it to a separate path first, run `PRAGMA integrity_check;`, and
only then replace the intended database using the normal recovery procedure.
Never overwrite the only known-good database during validation.

SQLite cannot express a native exclusion constraint for overlapping date
intervals. The application serializes new-booking writes with `BEGIN IMMEDIATE`
and performs the final overlap read inside that transaction. Direct SQL writes,
older code that bypasses `BookingService.create_booking_result`, and edits to an
existing booking interval remain outside that guarantee and require separate
controls and review.
