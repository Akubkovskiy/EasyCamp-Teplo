# Codex Repository Guidance

## Scope and read-first routing

This repository owns the production EasyCamp booking bot and live reservation
state. Treat every change that can affect bookings, synchronization, scheduled
jobs, or external integrations as production-sensitive.

Before editing:

1. Read `STATUS.md` and `INDEX.md`.
2. Read only the task-specific code and documentation identified by `INDEX.md`.
3. For database, backup, or restore work, also read `ops/backup.md`,
   `ops/restore.md`, `app/services/backup_service.py`, and the relevant Alembic
   migration/configuration files.
4. For deployment work, also read `ops/deploy.md`, `docker-compose.yml`,
   `.env.example`, and `docs/DEPLOYMENT.md`.
5. If the work changes the public-site integration boundary, inspect the
   corresponding `teplo-v-arkhyze` project guidance before deciding which
   repository owns the change.

## State and safety

- Never print, copy into Git, or expose values from `.env` or
  `google-credentials.json`.
- Treat `data/easycamp.db`, mounted logs, credentials, and runtime configuration
  outside Git as persistent production state. Do not assume they are disposable.
- Do not edit or replace the live SQLite file directly. Before a schema change,
  restore, or state-changing repair, identify the exact database path, create
  and verify a backup, define the rollback path, and confirm code/schema
  compatibility.
- Keep scheduler and synchronization effects explicit during restore validation.
  Avoid startup replay or duplicate synchronization against restored data.
- Changes to reservation ingestion, Avito sync, Google sync, overlap checks,
  duplicate guards, or scheduler startup must preserve idempotency and must not
  create double-booking windows.
- Prefer small, reviewable patches and preserve unrelated working-tree changes.

## Deployment and rollback

- Treat deployment as a stateful operation, not just a code rebuild. Confirm the
  Git revision, state backup, credential mounts, and database path before
  changing production.
- Validate Compose configuration before deployment. Rebuild or restart only the
  service required by the change. Do not use broad restarts or routine
  `docker compose down` / `docker compose down -v` operations.
- Define rollback before deploying booking, sync, scheduler, migration, backup,
  or restore changes. Code rollback and database rollback are separate actions;
  never overwrite good live data merely to match an older commit.
- Follow `ops/deploy.md` for deployment and `ops/restore.md` for recovery rather
  than improvising server commands.

After a deploy or restore, verify that the container is healthy, the bot
responds, database and credential paths resolve, and startup synchronization
does not create duplicate or conflicting reservations.

## Verification

Run the smallest relevant tests first, then the repository baseline when the
change warrants it:

```bash
ruff check app/
python -m pytest -q tests/
docker compose config --quiet
```

For booking, webhook, or synchronization changes, include the matching focused
tests (especially overlap and duplicate-guard coverage). If an external service
or credential is unavailable, report that limitation; do not treat a mocked or
skipped integration check as production verification.
