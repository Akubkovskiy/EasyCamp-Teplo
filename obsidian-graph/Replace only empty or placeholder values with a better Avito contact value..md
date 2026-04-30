---
source_file: "app\services\booking_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L65"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Replace only empty or placeholder values with a better Avito contact value.

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
- [[should_replace_avito_guest_value()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking