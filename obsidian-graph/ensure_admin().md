---
source_file: "scripts\verify_settings.py"
type: "code"
community: "login() / get_password_hash()"
location: "L21"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/login()_/_get_password_hash()
---

# ensure_admin()

## Connections
- [[User]] - `calls` [INFERRED]
- [[get_password_hash()]] - `calls` [INFERRED]
- [[verify_settings.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/login()_/_get_password_hash()