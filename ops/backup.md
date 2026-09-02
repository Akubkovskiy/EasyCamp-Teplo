# EasyCamp Backup

## Critical state

- `data/easycamp.db`
- `logs/`
- `.env`
- `google-credentials.json`
- any backup or restore behavior implemented in `app/services/backup_service.py`

## Backup rule

This repo already contains application-level backup logic.
Do not change backup or restore behavior casually without checking:
- DB path assumptions
- credentials path handling
- overwrite behavior during restore

## Recovery linkage

Use `ops/restore.md` as the restore baseline.
Use `docs/DEPLOYMENT.md` for deeper deployment detail.

## Booking-integrity migration checkpoint

Before revision `c8b1a6f4d2e9` is applied:

1. Pause application writers and scheduler-driven ingestion.
2. Create a consistent SQLite snapshot with SQLite's backup API, for example:
   `sqlite3 data/easycamp.db ".backup 'data/easycamp-before-c8b1a6f4d2e9.db'"`.
3. Run `PRAGMA integrity_check;` against the snapshot and confirm it returns `ok`.
4. Check for legacy duplicate identities:
   `SELECT source, external_id, COUNT(*) FROM bookings WHERE external_id IS NOT NULL GROUP BY source, external_id HAVING COUNT(*) > 1;`.

The migration aborts without deleting or merging rows when duplicates exist.
Reconcile duplicates manually from the verified snapshot before retrying.

The existing Drive backup implementation uploads the live database file directly.
Do not treat that best-effort upload as the migration checkpoint unless a restore
test has shown the uploaded SQLite file is consistent.
