---
source_file: "app\services\avito_sync_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L58"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Синхронизация броней из Avito для одного объявления      Args:         item_i

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[sync_avito_bookings()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking