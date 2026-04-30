---
source_file: "app\services\backup_service.py"
type: "rationale"
community: "on_startup() / AutoSyncMiddleware"
location: "L14"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/on_startup()_/_AutoSyncMiddleware
---

# Creates a backup of the SQLite database and uploads it to Google Drive.

## Connections
- [[backup_database_to_drive()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/on_startup()_/_AutoSyncMiddleware