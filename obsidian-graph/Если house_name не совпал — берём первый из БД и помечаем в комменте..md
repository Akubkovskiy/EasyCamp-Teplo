---
source_file: "tests\test_site_leads.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L196"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Если house_name не совпал — берём первый из БД и помечаем в комменте.

## Connections
- [[Base]] - `uses` [INFERRED]
- [[Booking]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[test_house_fallback_when_name_unknown()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking