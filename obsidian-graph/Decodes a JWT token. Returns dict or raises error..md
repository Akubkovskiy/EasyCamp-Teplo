---
source_file: "app\core\security.py"
type: "rationale"
community: "login() / get_password_hash()"
location: "L28"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/login()_/_get_password_hash()
---

# Decodes a JWT token. Returns dict or raises error.

## Connections
- [[decode_access_token()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/login()_/_get_password_hash()