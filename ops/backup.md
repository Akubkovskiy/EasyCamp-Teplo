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
