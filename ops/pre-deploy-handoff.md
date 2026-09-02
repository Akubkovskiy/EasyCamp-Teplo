# EasyCamp Hardening Pre-deploy Handoff

This is a release-candidate checklist, not authorization to deploy. The reviewed
scope is the booking-integrity, SQLite recovery, CI/readiness, and dependency
hardening series on `codex/booking-integrity-stage1`.

## Candidate evidence

- [ ] Use a clean checkout of the reviewed branch and record the exact HEAD SHA.
- [ ] GitHub Actions `quality`, `security`, and `docker` jobs are green for that SHA.
- [ ] `python scripts/verify_release.py --with-docker --image-tag easycamp:<SHA>` passes
      on Python 3.11 with Docker available.
- [ ] `pip-audit -r requirements.txt` reports no known vulnerabilities.
- [ ] Record the built image ID/digest; keep the previously running image/tag.
- [ ] Confirm `SECRET_KEY` is at least 32 random bytes. Preserve the current key
      unless intentionally invalidating every existing admin session.

## State and migration

- [ ] Resolve and record the real host path mounted at `/app/data/easycamp.db`.
- [ ] Confirm every normal and maintenance `RESTORE_*` flag is false/empty.
- [ ] Stop all EasyCamp writers without `docker compose down`.
- [ ] Create and validate a SQLite API snapshot; record SHA-256, booking count,
      active date range, and current Alembic revision.
- [ ] Run the duplicate preflight from `ops/backup.md`. Do not alter or delete
      duplicate rows during the release window.
- [ ] Apply `alembic upgrade head` only after the snapshot and preflight pass.
- [ ] Confirm `uq_bookings_source_external_id` is unique over
      `(source, external_id)` and `/ready` validates all `House`/`Booking` columns.

## Bounded start and canaries

- [ ] Recreate only the `app` service from the recorded candidate image.
- [ ] Confirm `/health` and `/ready` return 200 and the container stays healthy
      without a restart loop.
- [ ] Confirm SQLite integrity and compare booking count/date range to the snapshot.
- [ ] Confirm exactly one scheduler and one Telegram polling process in logs.
- [ ] Run a private/admin bot canary during an operator-controlled quiet window.
- [ ] Keep scheduled sync flags off and hold Site/Avito HTTP ingress at the edge
      during initial validation; there is no global ingestion kill switch.
- [ ] Re-enable each independently controlled source in sequence and verify
      replays resolve as duplicates and create no overlap window.

## Rollback decision

- Code/runtime failure before new writes: stop `app`, return to the previous
  image/tag, downgrade `c8b1a6f4d2e9` if the previous code does not own the
  index, and rerun health/integrity canaries.
- Suspected data mutation or restore issue: keep writers stopped and follow
  `ops/restore.md` using the validated snapshot. Never raw-copy a live SQLite file.
- Retain the previous image and snapshot until booking and ingestion canaries are
  accepted by the operator.
