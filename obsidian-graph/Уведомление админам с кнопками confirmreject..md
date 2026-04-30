---
source_file: "app\telegram\handlers\guest_booking.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L111"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Уведомление админам с кнопками confirm/reject.

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingCreate]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[HouseService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[_send_admin_booking_notification()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking