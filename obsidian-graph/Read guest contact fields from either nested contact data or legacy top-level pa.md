---
source_file: "app\services\booking_service.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L28"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Read guest contact fields from either nested contact data or legacy top-level pa

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
- [[extract_avito_contact_value()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking