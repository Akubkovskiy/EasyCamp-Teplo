---
source_file: "app\services\avito_sync_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L23"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Read Avito guest contact fields from nested contact or legacy top-level payload

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[extract_avito_contact_field()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking