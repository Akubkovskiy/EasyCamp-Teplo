---
source_file: "tests\test_site_leads.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L146"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Если SITE_LEAD_TOKEN пустой в settings — endpoint 503.

## Connections
- [[Base]] - `uses` [INFERRED]
- [[Booking]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[test_disabled_when_token_unset()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking