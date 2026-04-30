---
source_file: "app\services\backup_service.py"
type: "rationale"
community: "on_startup() / AutoSyncMiddleware"
location: "L80"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/on_startup()_/_AutoSyncMiddleware
---

# Checks Google Drive for the latest backup and restores it     ONLY if the local

## Connections
- [[restore_latest_backup()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/on_startup()_/_AutoSyncMiddleware