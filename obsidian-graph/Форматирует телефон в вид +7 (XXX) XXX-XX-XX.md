---
source_file: "app\web\routers\booking_web.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L19"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Форматирует телефон в вид +7 (XXX) XXX-XX-XX

## Connections
- [[BookingCreate]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[BookingUpdate]] - `uses` [INFERRED]
- [[HouseService]] - `uses` [INFERRED]
- [[format_phone()_1]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking