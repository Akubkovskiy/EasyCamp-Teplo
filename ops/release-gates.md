# EasyCamp Release Gates

This checklist is the repository-side release contract. Passing it does not
authorize a production deploy, migration, restart, or restore.

## 1. Local and CI gates

- [ ] Install `requirements-dev.txt` (which includes `requirements.txt`) on Python 3.11.
- [ ] Run `python scripts/verify_release.py` successfully.
- [ ] Confirm the GitHub Actions `quality`, `security`, and `docker` jobs are green.
- [ ] Confirm Alembic reports exactly one head.
- [ ] Review every migration and its downgrade; do not rely on `create_all()` as
      a migration mechanism.

The verifier runs the full test suite, byte-compilation, dependency consistency,
a repo-wide fatal-error lint baseline, and stricter E/F lint over the booking,
backup/restore, and readiness paths. Existing repository lint debt is not hidden
as a claim of full strict compliance.

## 2. Docker-capable gate

This gate is mandatory even when development happened on a host without Docker:

```sh
# Run in an isolated clean release-check checkout, never over a real .env.
cp .env.example .env
python scripts/verify_release.py \
  --with-docker \
  --image-tag easycamp:<reviewed-commit-sha>
```

- [ ] `docker compose config --quiet` succeeds with the intended environment.
- [ ] The image builds from the reviewed commit and its immutable image ID/digest
      is recorded.
- [ ] `.env`, credentials, SQLite files, logs, virtualenvs, and generated graphs
      are absent from the build context/image.
- [ ] `EASYCAMP_IMAGE_TAG` is the reviewed commit SHA or an immutable release tag,
      not `local`.

Do not use a release-check `.env` for production and do not commit it.

## 3. State and migration gate

- [ ] Resolve the exact production `DATABASE_URL` and mounted host path.
- [ ] Stop or pause every booking writer before a schema change.
- [ ] Create a validated SQLite backup through `ops/backup.md` and record SHA-256.
- [ ] Run the stage 1 duplicate preflight before migration `c8b1a6f4d2e9`.
- [ ] Apply Alembic migrations only after the backup and preflight are accepted.
- [ ] For the known house-4 graph, follow `ops/house4-remediation.md`; require
      exact row-ID matching, the forensic snapshot checksum, and zero remaining
      foreign-key violations before startup.
- [ ] Confirm `RESTORE_FROM_DRIVE_ENABLED=false`,
      `RESTORE_MAINTENANCE_MODE=false`, `RESTORE_ALLOW_OVERWRITE=false`, and an
      empty `RESTORE_DRIVE_FILE_ID` for normal startup.
- [ ] Set `INGESTION_MAINTENANCE_MODE=true` only for the bounded database-ready
      canary, then set it explicitly to `false` when enabling normal writers.

## 4. Compose-change review gate

Before this compose hardening is first applied, explicitly review:

- `restart: unless-stopped` replacing `always`
- DB-aware `/ready` healthcheck timing and failure behavior
- read-only Google credential mount
- commit-addressable `EASYCAMP_IMAGE_TAG`
- the portless, one-shot `maintenance` restore profile
- `python:3.11-slim-bookworm` as the Docker base line

These are repository proposals until a separately authorized deployment uses
them. Do not recreate the production container merely to test the YAML.

## 5. Post-start canaries

- [ ] `/health` returns `200` (process liveness).
- [ ] `/ready` returns `200`, reports the external-booking identity index, and
      has validated every ORM column used by the `House` and `Booking` models.
- [ ] `/ready` reports no referential-integrity failure; active house inventory
      excludes the archived house.
- [ ] The first `/ready` canary reports `"ingestion":"maintenance"`, all other
      HTTP routes return 503, and logs contain no scheduler, sync, or polling start.
- [ ] The container reaches `healthy` without a restart loop.
- [ ] SQLite `PRAGMA integrity_check` returns `ok`.
- [ ] Active booking counts/date ranges match the pre-change checkpoint.
- [ ] Telegram responds in the intended private/admin context.
- [ ] Logs show one scheduler and one polling process, not duplicates.
- [ ] After database validation, recreate only `app` with
      `INGESTION_MAINTENANCE_MODE=false`; re-enable each independently controlled
      source in sequence and inspect replay results.

## 6. Rollback gate

- [ ] Keep the previous image/tag and validated DB snapshot until canaries pass.
- [ ] Know whether rollback is code-only or code plus schema/data.
- [ ] Stop writers before any database rollback.
- [ ] Use `ops/restore.md` for database recovery; never raw-copy a live SQLite file.
- [ ] Re-run `/health`, `/ready`, integrity, booking-count, and ingestion canaries
      after rollback.
