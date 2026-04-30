---
source_file: "app\api\site_leads.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L1"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Site lead intake endpoint (Phase S10.1).  Принимает заявки с публичного сайта `t

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingCreate]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[site_leads.py]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking