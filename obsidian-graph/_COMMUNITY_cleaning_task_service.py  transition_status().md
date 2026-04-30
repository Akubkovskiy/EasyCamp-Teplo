---
type: community
cohesion: 0.27
members: 11
---

# cleaning_task_service.py / transition_status()

**Cohesion:** 0.27 - loosely connected
**Members:** 11 nodes

## Members
- [[_accrue_cleaning_fee()]] - code - app\services\cleaning_task_service.py
- [[add_photo()]] - code - app\services\cleaning_task_service.py
- [[can_transition()]] - code - app\services\cleaning_task_service.py
- [[cleaning_task_service.py]] - code - app\services\cleaning_task_service.py
- [[completion_requirements_ok()]] - code - app\services\cleaning_task_service.py
- [[create_task_for_booking()]] - code - app\services\cleaning_task_service.py
- [[ensure_default_checklist()]] - code - app\services\cleaning_task_service.py
- [[open_supply_alert()]] - code - app\services\cleaning_task_service.py
- [[resolve_supply_alerts()]] - code - app\services\cleaning_task_service.py
- [[toggle_check()]] - code - app\services\cleaning_task_service.py
- [[transition_status()]] - code - app\services\cleaning_task_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/cleaning_task_service.py_/_transition_status()
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_BookingStatus  Booking]]

## Top bridge nodes
- [[cleaning_task_service.py]] - degree 11, connects to 1 community
- [[ensure_default_checklist()]] - degree 4, connects to 1 community
- [[_accrue_cleaning_fee()]] - degree 3, connects to 1 community
- [[create_task_for_booking()]] - degree 3, connects to 1 community
- [[add_photo()]] - degree 2, connects to 1 community