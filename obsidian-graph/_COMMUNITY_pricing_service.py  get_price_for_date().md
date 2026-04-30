---
type: community
cohesion: 0.24
members: 11
---

# pricing_service.py / get_price_for_date()

**Cohesion:** 0.24 - loosely connected
**Members:** 11 nodes

## Members
- [[calculate_stay_total()]] - code - app\services\pricing_service.py
- [[check_and_apply_auto_discounts()]] - code - app\services\pricing_service.py
- [[create_discount()]] - code - app\services\pricing_service.py
- [[create_price()]] - code - app\services\pricing_service.py
- [[deactivate_discount()]] - code - app\services\pricing_service.py
- [[delete_price()]] - code - app\services\pricing_service.py
- [[get_active_discounts()]] - code - app\services\pricing_service.py
- [[get_display_price()]] - code - app\services\pricing_service.py
- [[get_price_for_date()]] - code - app\services\pricing_service.py
- [[get_prices_for_house()]] - code - app\services\pricing_service.py
- [[pricing_service.py]] - code - app\services\pricing_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/pricing_service.py_/_get_price_for_date()
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_BookingStatus  Booking]]

## Top bridge nodes
- [[pricing_service.py]] - degree 11, connects to 1 community
- [[create_discount()]] - degree 3, connects to 1 community
- [[create_price()]] - degree 2, connects to 1 community