---
source_file: "app\telegram\handlers\guest_booking.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L251"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Контакт получен в self-service потоке (не login). Создаём User     с ролью GUEST

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
- [[guest_book_contact()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking