---
source_file: "tests\test_avito_overlap_guard.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L62"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# When a new Avito booking overlaps an existing one, it must NOT be created.

## Connections
- [[BookingService]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking