---
type: community
cohesion: 0.27
members: 13
---

# test_site_leads.py / _payload()

**Cohesion:** 0.27 - loosely connected
**Members:** 13 nodes

## Members
- [[_payload()]] - code - tests\test_site_leads.py
- [[client()]] - code - tests\test_site_leads.py
- [[seeded_house()]] - code - tests\test_site_leads.py
- [[session_factory()]] - code - tests\test_site_leads.py
- [[test_create_lead_creates_booking()]] - code - tests\test_site_leads.py
- [[test_disabled_when_token_unset()]] - code - tests\test_site_leads.py
- [[test_house_fallback_when_name_unknown()]] - code - tests\test_site_leads.py
- [[test_idempotent_on_external_ref()]] - code - tests\test_site_leads.py
- [[test_invalid_dates_422()]] - code - tests\test_site_leads.py
- [[test_missing_token_401()]] - code - tests\test_site_leads.py
- [[test_no_houses_in_db_returns_422()]] - code - tests\test_site_leads.py
- [[test_site_leads.py]] - code - tests\test_site_leads.py
- [[test_wrong_token_401()]] - code - tests\test_site_leads.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_site_leads.py_/__payload()
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_BookingStatus  Booking]]

## Top bridge nodes
- [[test_site_leads.py]] - degree 13, connects to 1 community
- [[seeded_house()]] - degree 4, connects to 1 community
- [[session_factory()]] - degree 3, connects to 1 community
- [[test_disabled_when_token_unset()]] - degree 3, connects to 1 community
- [[test_house_fallback_when_name_unknown()]] - degree 3, connects to 1 community