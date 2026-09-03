# Archived House 4 Remediation

## Scope

This is the only approved data shape for the one-time repair implemented by
`app.services.house_integrity_service`:

- missing parent: `houses.id = 4`
- `bookings`: IDs `31`, `59`, `75`
- `cleaning_tasks`: IDs `2`, `20`, `40`
- `supply_alerts`: ID `1`
- no other foreign-key violations

The repair does not delete or repoint these rows. It inserts one inactive
archival parent after revision `f2a4c6e8b0d1` adds `houses.is_active`.
Any drift from the IDs above aborts both snapshot validation and repair.

This runbook is not authorization to mutate production.

## Preconditions

1. Record the reviewed commit SHA, candidate image ID, previous image ID, and
   previous live commit.
2. Complete `ops/release-gates.md`, including the Docker-capable build.
3. Confirm the read-only audit still reports the exact graph above:

   ```sh
   docker run --rm --network none \
     -v /root/easycamp-bot/data:/app/data:ro \
     easycamp:<SHA> \
     python -m app.services.house_integrity_service \
       validate-known-house4 /app/data/easycamp.db
   ```

4. Confirm there are no `(source, external_id)` duplicates.
5. Arrange a quiet window. Use `INGESTION_MAINTENANCE_MODE=true` so HTTP
   application routes, Telegram polling, scheduler, and startup sync remain
   disabled until the database and process canaries pass.

## Snapshot, migrate, repair

1. Stop only the EasyCamp writer; never use `docker compose down`:

   ```sh
   docker compose stop app
   ```

2. Confirm no process/container still mounts the database and no
   `easycamp.db-wal`, `easycamp.db-shm`, or `easycamp.db-journal` exists. Do not
   delete sidecars to bypass this gate.
3. Create the forensic rollback snapshot with a new timestamped filename:

   ```sh
   docker run --rm --network none \
     -v /root/easycamp-bot/data:/app/data \
     easycamp:<SHA> \
     python -m app.services.house_integrity_service \
       snapshot-known-house4 \
       /app/data/easycamp.db \
       /app/data/easycamp.pre-house4-<UTC timestamp>.db
   ```

   Record the emitted SHA-256. Unlike a normal application backup, this
   forensic snapshot deliberately preserves the seven audited violations and
   refuses every other invalid shape.

4. Apply reviewed migrations from the same candidate image:

   ```sh
   docker run --rm --network none \
     -v /root/easycamp-bot/data:/app/data \
     easycamp:<SHA> \
     python -m alembic upgrade head
   ```

5. Repair only the known parent row, using the recorded checksum:

   ```sh
   docker run --rm --network none \
     -v /root/easycamp-bot/data:/app/data \
     easycamp:<SHA> \
     python -m app.services.house_integrity_service \
       repair-known-house4 \
       /app/data/easycamp.db \
       /app/data/easycamp.pre-house4-<UTC timestamp>.db \
       --maintenance \
       --expected-snapshot-checksum <SHA-256>
   ```

6. While writers remain stopped, require all of these:

   - `PRAGMA integrity_check = ok`
   - `PRAGMA foreign_key_check` returns zero rows
   - Alembic head is `f2a4c6e8b0d1`
   - `houses.id=4` exists with `is_active=0`
   - active houses remain IDs `1`, `2`, `3`
   - booking count and date range match the checkpoint
   - `uq_bookings_source_external_id` is unique on `(source, external_id)`

Only then recreate the `app` service in ingestion maintenance mode:

```sh
INGESTION_MAINTENANCE_MODE=true EASYCAMP_IMAGE_TAG=<SHA> \
  docker compose up -d --no-deps --force-recreate app
```

Require `/health` to return 200 and `/ready` to return 200 with
`"ingestion":"maintenance"`. All other HTTP routes must return 503, and logs
must show no scheduler, sync, or Telegram polling startup.

After those canaries pass, recreate only `app` with the gate explicitly off:

```sh
INGESTION_MAINTENANCE_MODE=false EASYCAMP_IMAGE_TAG=<SHA> \
  docker compose up -d --no-deps --force-recreate app
```

Then run the private bot, scheduler, polling, and sequential source canaries.
Do not use `docker compose down` at any stage.

## Full rollback

A code-only rollback is unsafe: the previous application does not understand
`houses.is_active` and would expose the archival row as inventory.

With every writer stopped, atomically restore the forensic snapshot using the
candidate image and recorded checksum:

```sh
docker run --rm --network none \
  -v /root/easycamp-bot/data:/app/data \
  easycamp:<SHA> \
  python -m app.services.house_integrity_service \
    restore-known-house4-snapshot \
    /app/data/easycamp.pre-house4-<UTC timestamp>.db \
    /app/data/easycamp.db \
    --maintenance \
    --expected-candidate-checksum <FORENSIC-SNAPSHOT-SHA-256> \
    --expected-target-checksum <REPAIRED-DATABASE-SHA-256>
```

The rollback command first retains a strict, valid forward snapshot of the
repaired database, then atomically reinstalls the exact audited pre-repair
state. Return to the recorded previous image/commit before starting writers.
If the repaired database checksum changed after the repair, automatic rollback
refuses to run so that post-start booking writes cannot be silently discarded.
The old state will again contain the known seven violations, so the hardening
release remains blocked until another approved repair attempt.
