---
source_file: "tests\test_avito_overlap_guard.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L166"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Checkout day == next checkin day is NOT an overlap (adjacent bookings OK).

## Connections
- [[BookingService]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking