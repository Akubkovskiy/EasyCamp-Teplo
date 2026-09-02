# EasyCamp Restore

## Safety contract

Restore is a separate maintenance operation, not automatic startup recovery.
It must not run beside FastAPI booking writes, Telegram polling, the scheduler,
Avito/Sheets/Yandex ingestion, price sync, or automatic discounts.

The implementation fails closed unless all of these are true:

- `RESTORE_FROM_DRIVE_ENABLED=true`
- `RESTORE_MAINTENANCE_MODE=true`
- `RESTORE_DRIVE_FILE_ID` identifies the exact approved backup
- all sync/automation flags listed below are `false`
- a non-empty target is overwritten only with
  `RESTORE_ALLOW_OVERWRITE=true`
- no `easycamp.db-wal`, `easycamp.db-shm`, or `easycamp.db-journal` exists
- Drive checksum, SQLite integrity, foreign keys, and minimum schema validate

The recommended Compose `restore` service is a portless one-shot process with
`restart: "no"`; it exits after one attempt and never initializes FastAPI,
the scheduler, sync middleware, bot commands, or Telegram polling. If the main
app is started with maintenance flags instead, only `/health` remains exposed
and every other HTTP route returns 503.

## Required operator decisions

Record these before changing runtime state:

1. Exact Drive file ID, filename, timestamp, and expected checksum.
2. Exact target path resolved from `DATABASE_URL`.
3. Whether an existing non-empty target is approved for replacement.
4. Who will validate restored booking counts/date ranges before writers resume.

Do not choose a backup merely because it is the newest file.

## Drive restore runbook

1. Stop the normal app container without running `docker compose down`:

   ```sh
   docker compose stop app
   ```

2. Confirm no other process/container mounts the same SQLite file. Inspect for
   `-wal`, `-shm`, and `-journal` sidecars. Do not delete them to bypass the
   gate; their presence is evidence that shutdown/checkpoint state needs review.

3. Set the following maintenance environment:

   ```dotenv
   RESTORE_FROM_DRIVE_ENABLED=true
   RESTORE_MAINTENANCE_MODE=true
   RESTORE_DRIVE_FILE_ID=<approved-drive-file-id>
   RESTORE_ALLOW_OVERWRITE=false
   ENABLE_AUTO_SYNC=false
   SYNC_ON_BOT_START=false
   SYNC_ON_USER_INTERACTION=false
   ENABLE_YANDEX_TRAVEL_SYNC=false
   ENABLE_YANDEX_TRAVEL_PRICE_SYNC=false
   ENABLE_AVITO_PRICE_SYNC=false
   ENABLE_AUTO_DISCOUNTS=false
   ```

   Change `RESTORE_ALLOW_OVERWRITE` to `true` only after approving replacement
   of a non-empty target. That path first creates a validated rollback snapshot
   named `easycamp.pre-restore-<UTC timestamp>-<id>.db` beside the target.

4. Run the dedicated one-shot maintenance service:

   ```sh
   docker compose --profile maintenance run --rm restore
   ```

   A successful exit prints the selected Drive ID, installed SHA-256, and
   rollback path. Any exception returns non-zero. Do not enable normal flags
   after a failed run, and do not run the command while `app` is active.

5. Set every restore flag back to `false` and clear
   `RESTORE_DRIVE_FILE_ID`. Keep sync flags off for validation.

6. Validate the installed file while no application process is running:

   ```sh
   docker compose --profile maintenance run --rm restore \
     python -m app.services.sqlite_recovery validate /app/data/easycamp.db
   ```

7. Compare house/booking counts, active booking date ranges, and external
   identities with the recovery record. If the backup predates the current
   Alembic head, take another checkpoint and run the reviewed migration before
   starting this code. Schema validation intentionally does not auto-migrate.

8. Start the normal app with restore flags off and sync flags still off. Run
   read-only DB/health and bot canaries. Re-enable ingestion one source at a
   time only after the restored state is accepted.

## Atomicity and rollback

Drive bytes are downloaded to an application-owned temporary directory. The
candidate checksum and schema are validated, then SQLite's backup API creates a
second staged database in the target directory. `os.replace` performs the
same-filesystem atomic swap. The Drive candidate and pre-restore rollback file
are never used as the live file and are not deleted by the restore function.

To roll back, stop every writer again and use the retained snapshot as a local
candidate. The command creates another rollback snapshot before replacing the
current target:

```sh
docker compose --profile maintenance run --rm restore \
  python -m app.services.sqlite_recovery restore-local \
  /app/data/easycamp.pre-restore-<timestamp>-<id>.db \
  /app/data/easycamp.db \
  --maintenance --allow-overwrite
```

Validate the result before normal startup. Never use a raw filesystem copy as
the rollback mechanism.

## Booking-integrity migration rollback

Revision `c8b1a6f4d2e9` only adds
`uq_bookings_source_external_id`; it does not rewrite booking rows. With every
writer stopped, `alembic downgrade a1b2c3d4e5f6` removes the index. Verify with
`PRAGMA index_list('bookings')`, return to the previous application revision,
and run a read-only booking canary.

SQLite cannot express a native exclusion constraint for overlapping date
intervals. Direct SQL writes, older code that bypasses the booking service, and
edits to an existing booking interval remain outside the stage 1 guarantee.
