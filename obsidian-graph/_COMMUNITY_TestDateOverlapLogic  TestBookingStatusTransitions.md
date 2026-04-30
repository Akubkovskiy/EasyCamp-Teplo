---
type: community
cohesion: 0.09
members: 22
---

# TestDateOverlapLogic / TestBookingStatusTransitions

**Cohesion:** 0.09 - loosely connected
**Members:** 22 nodes

## Members
- [[.test_adjacent_ranges_no_overlap()]] - code - tests\test_booking_service.py
- [[.test_checked_in_to_completed_on_checkout_day()]] - code - tests\test_booking_service.py
- [[.test_completely_after()]] - code - tests\test_booking_service.py
- [[.test_completely_before()]] - code - tests\test_booking_service.py
- [[.test_confirmed_to_checking_in_on_checkin_day()]] - code - tests\test_booking_service.py
- [[.test_contained_within()]] - code - tests\test_booking_service.py
- [[.test_no_transition_during_stay()]] - code - tests\test_booking_service.py
- [[.test_overlapping_ranges()]] - code - tests\test_booking_service.py
- [[Adjacent ranges (checkout = next checkin) should NOT overlap]] - rationale - tests\test_booking_service.py
- [[Booking should transition to CHECKING_IN on check-in day]] - rationale - tests\test_booking_service.py
- [[Booking should transition to COMPLETED onafter checkout day]] - rationale - tests\test_booking_service.py
- [[No transition to COMPLETED during the stay]] - rationale - tests\test_booking_service.py
- [[Request completely after existing - no overlap]] - rationale - tests\test_booking_service.py
- [[Request completely before existing - no overlap]] - rationale - tests\test_booking_service.py
- [[Request fully contained within existing - overlap]] - rationale - tests\test_booking_service.py
- [[Test booking status transition logic]] - rationale - tests\test_booking_service.py
- [[Test the date overlap detection logic used in availability checks]] - rationale - tests\test_booking_service.py
- [[TestBookingStatusTransitions]] - code - tests\test_booking_service.py
- [[TestDateOverlapLogic]] - code - tests\test_booking_service.py
- [[Two ranges that overlap should be detected]] - rationale - tests\test_booking_service.py
- [[Unit tests for booking service logic]] - rationale - tests\test_booking_service.py
- [[test_booking_service.py]] - code - tests\test_booking_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/TestDateOverlapLogic_/_TestBookingStatusTransitions
SORT file.name ASC
```
