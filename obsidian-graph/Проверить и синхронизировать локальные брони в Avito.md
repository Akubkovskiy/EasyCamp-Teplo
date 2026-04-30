---
source_file: "app\jobs\avito_sync_job.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L64"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Проверить и синхронизировать локальные брони в Avito

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[verify_local_bookings_in_avito()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking