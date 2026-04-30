---
source_file: "app\web\deps.py"
type: "rationale"
community: "login() / get_password_hash()"
location: "L47"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/login()_/_get_password_hash()
---

# Same as above but redirects to login page on failure.     Used for page routes.

## Connections
- [[User]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[get_current_admin_or_redirect()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/login()_/_get_password_hash()