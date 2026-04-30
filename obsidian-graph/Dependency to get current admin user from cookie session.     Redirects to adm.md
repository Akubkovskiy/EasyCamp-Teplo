---
source_file: "app\web\deps.py"
type: "rationale"
community: "login() / get_password_hash()"
location: "L15"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/login()_/_get_password_hash()
---

# Dependency to get current admin user from cookie session.     Redirects to /adm

## Connections
- [[User]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[get_current_admin()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/login()_/_get_password_hash()