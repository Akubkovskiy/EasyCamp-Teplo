---
source_file: "app\jobs\status_updater_job.py"
type: "rationale"
community: "BookingStatus / Booking"
location: "L16"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# Автоматическое обновление статусов броней:     - CONFIRMED/PAID -> CHECKED_IN (

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[update_booking_statuses_job()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/BookingStatus_/_Booking