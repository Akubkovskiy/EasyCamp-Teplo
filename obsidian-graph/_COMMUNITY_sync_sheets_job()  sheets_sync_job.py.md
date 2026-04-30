---
type: community
cohesion: 0.50
members: 4
---

# sync_sheets_job() / sheets_sync_job.py

**Cohesion:** 0.50 - moderately connected
**Members:** 4 nodes

## Members
- [[sheets_sync_job.py]] - code - app\jobs\sheets_sync_job.py
- [[sync_sheets_job()]] - code - app\jobs\sheets_sync_job.py
- [[Периодическая задача синхронизации с Google Sheets]] - rationale - app\jobs\sheets_sync_job.py
- [[Периодическая синхронизация с Google Sheets с retry логикой]] - rationale - app\jobs\sheets_sync_job.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/sync_sheets_job()_/_sheets_sync_job.py
SORT file.name ASC
```
