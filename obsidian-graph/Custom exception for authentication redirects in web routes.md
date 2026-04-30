---
source_file: "app\web\deps.py"
type: "rationale"
community: "login() / get_password_hash()"
location: "L7"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/login()_/_get_password_hash()
---

# Custom exception for authentication redirects in web routes

## Connections
- [[AuthRedirectException]] - `rationale_for` [EXTRACTED]
- [[User]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/login()_/_get_password_hash()