---
source_file: "app\jobs\avito_sync_job.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L1"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Периодическая задача синхронизации с Avito API

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[avito_sync_job.py]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking