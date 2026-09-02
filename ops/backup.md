# EasyCamp Backup

## Critical state

- `data/easycamp.db`
- `.env`
- `google-credentials.json`
- logs needed to reconstruct the incident timeline

Never back up a running SQLite database with `cp`, `Copy-Item`, `docker cp`, or
a direct upload of `easycamp.db`. A live database may have committed pages in
its WAL that are absent from the main file.

## Application backup behavior

`app/services/backup_service.py` now performs these steps:

1. Resolve `DATABASE_URL` with SQLAlchemy's URL parser.
2. Use SQLite's online backup API to create a transactionally consistent
   temporary snapshot.
3. Require `PRAGMA integrity_check = ok`, no foreign-key violations, and the
   minimum EasyCamp `houses`/`bookings` schema.
4. Calculate SHA-256 and upload the snapshot, never the live database file.
5. Store SHA-256, size, schema format, and Alembic revision in Drive
   `appProperties` and fail the scheduled job if any step fails.

The temporary snapshot is application-owned and removed after upload. The
source database is not moved, rewritten, or deleted.

## Manual snapshot checkpoint

Run this from a one-shot container or local environment that mounts the same
database but does not start FastAPI, Telegram polling, or the scheduler:

```powershell
python -m app.services.sqlite_recovery snapshot `
  /app/data/easycamp.db `
  /app/data/easycamp-before-change.db
```

The command prints JSON including SHA-256, size, tables, and schema revision.
Keep that output with the change record. The destination must be new or empty.

## Booking-integrity migration checkpoint

Before revision `c8b1a6f4d2e9` is applied:

1. Stop application writers and scheduler-driven ingestion.
2. Create and validate a consistent snapshot using the command above.
3. Check for legacy duplicate identities:

   ```sql
   SELECT source, external_id, COUNT(*)
   FROM bookings
   WHERE external_id IS NOT NULL
   GROUP BY source, external_id
   HAVING COUNT(*) > 1;
   ```

The migration aborts without deleting or merging rows when duplicates exist.
Reconcile duplicates manually from the verified snapshot before retrying.

## Restore testing

A Drive upload is not a proven backup until a separate-path restore has passed
checksum, integrity, foreign-key, and schema validation. Follow
`ops/restore.md`; never test by overwriting the only production database.
