---
source_file: "app\telegram\handlers\guest_booking.py"
type: "code"
community: "guest.py / safe_edit()"
location: "L250"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/guest.py_/_safe_edit()
---

# guest_book_contact()

## Connections
- [[_ask_guests_count()]] - `calls` [EXTRACTED]
- [[add_user()]] - `calls` [INFERRED]
- [[guest_booking.py]] - `contains` [EXTRACTED]
- [[normalize_phone()]] - `calls` [INFERRED]
- [[refresh_users_cache()]] - `calls` [INFERRED]
- [[set_guest_auth()]] - `calls` [INFERRED]
- [[set_guest_context()]] - `calls` [INFERRED]
- [[Контакт получен в self-service потоке (не login). Создаём User     с ролью GUEST]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/guest.py_/_safe_edit()