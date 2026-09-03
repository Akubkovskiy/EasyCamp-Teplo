# EasyCamp deployment pointer

This former quick-start document is superseded because EasyCamp deployment is
stateful and cannot safely be reduced to `git pull`, `restart`, or a raw copy of
the live SQLite file.

Use these canonical runbooks:

1. [`ops/release-gates.md`](ops/release-gates.md) — tests, CI, image, migration,
   and canary gates
2. [`ops/pre-deploy-handoff.md`](ops/pre-deploy-handoff.md) — ordered release-candidate handoff
3. [`ops/deploy.md`](ops/deploy.md) — bounded deployment entrypoint
4. [`ops/backup.md`](ops/backup.md) — consistent SQLite snapshots
5. [`ops/restore.md`](ops/restore.md) — maintenance-only atomic restore
6. [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — first-time integration setup

Passing the repository checks does not authorize a production deployment.
Before changing the FI runtime, require a separate approved plan with exact
commit/image, verified backup, migration preflight, canaries, and rollback.
