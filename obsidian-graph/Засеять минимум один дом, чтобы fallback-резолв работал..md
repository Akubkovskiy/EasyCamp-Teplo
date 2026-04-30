---
source_file: "tests\test_site_leads.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L60"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Засеять минимум один дом, чтобы fallback-резолв работал.

## Connections
- [[Base]] - `uses` [INFERRED]
- [[Booking]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[seeded_house()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking