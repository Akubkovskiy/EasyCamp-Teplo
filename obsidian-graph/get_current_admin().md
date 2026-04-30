---
source_file: "app\web\deps.py"
type: "code"
community: "login() / get_password_hash()"
location: "L14"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/login()_/_get_password_hash()
---

# get_current_admin()

## Connections
- [[Dependency to get current admin user from cookie session.     Redirects to adm]] - `rationale_for` [EXTRACTED]
- [[decode_access_token()]] - `calls` [INFERRED]
- [[deps.py]] - `contains` [EXTRACTED]
- [[get_current_admin_or_redirect()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/login()_/_get_password_hash()