---
source_file: "tests\test_avito_overlap_guard.py"
type: "rationale"
community: "test_avito_overlap_guard.py / process_avito_booking()"
location: "L285"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/test_avito_overlap_guard.py_/_process_avito_booking()
---

# Verify the SQL overlap condition: check_in < new_check_out AND check_out > new_c

## Connections
- [[BookingService]] - `uses` [INFERRED]
- [[TestOverlapCondition]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/test_avito_overlap_guard.py_/_process_avito_booking()