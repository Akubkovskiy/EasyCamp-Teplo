---
source_file: "app\services\avito_sync_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L1"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Сервис синхронизации броней из Avito API

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[avito_sync_service.py]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking