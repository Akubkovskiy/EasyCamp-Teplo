---
type: community
cohesion: 0.36
members: 10
---

# bookings.py / send_bookings_response()

**Cohesion:** 0.36 - loosely connected
**Members:** 10 nodes

## Members
- [[bookings.py]] - code - app\telegram\handlers\bookings.py
- [[send_bookings_response()]] - code - app\telegram\handlers\bookings.py
- [[show_active_bookings()]] - code - app\telegram\handlers\bookings.py
- [[show_all_bookings()]] - code - app\telegram\handlers\bookings.py
- [[show_bookings_list()]] - code - app\telegram\handlers\bookings.py
- [[show_bookings_menu()]] - code - app\telegram\handlers\bookings.py
- [[show_checked_in_bookings()]] - code - app\telegram\handlers\bookings.py
- [[show_checking_in_bookings()]] - code - app\telegram\handlers\bookings.py
- [[show_today_bookings()]] - code - app\telegram\handlers\bookings.py
- [[show_week_bookings()]] - code - app\telegram\handlers\bookings.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/bookings.py_/_send_bookings_response()
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 1 edge to [[_COMMUNITY_test_avito_overlap_guard.py  process_avito_booking()]]

## Top bridge nodes
- [[bookings.py]] - degree 10, connects to 1 community
- [[send_bookings_response()]] - degree 7, connects to 1 community
- [[show_all_bookings()]] - degree 3, connects to 1 community
- [[show_checked_in_bookings()]] - degree 3, connects to 1 community
- [[show_checking_in_bookings()]] - degree 3, connects to 1 community