---
source_file: "app\services\booking_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L340"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Получить бронь по ID с информацией о доме

## Connections
- [[AvitoBookingPayload]] - `uses` [INFERRED]
- [[Booking]] - `uses` [INFERRED]
- [[BookingCreate]] - `uses` [INFERRED]
- [[BookingSource]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[BookingUpdate]] - `uses` [INFERRED]
- [[CleaningPaymentEntryType]] - `uses` [INFERRED]
- [[CleaningPaymentLedger]] - `uses` [INFERRED]
- [[CleaningTask]] - `uses` [INFERRED]
- [[CleaningTaskStatus]] - `uses` [INFERRED]
- [[House]] - `uses` [INFERRED]
- [[PaymentStatus]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking