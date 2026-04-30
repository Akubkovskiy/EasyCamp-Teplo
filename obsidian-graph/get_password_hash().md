---
source_file: "app\core\security.py"
type: "code"
community: "login() / get_password_hash()"
location: "L11"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/login()_/_get_password_hash()
---

# get_password_hash()

## Connections
- [[Generates a hash from a plain password.]] - `rationale_for` [EXTRACTED]
- [[create_admin()]] - `calls` [INFERRED]
- [[ensure_admin()]] - `calls` [INFERRED]
- [[login()]] - `calls` [INFERRED]
- [[security.py]] - `contains` [EXTRACTED]
- [[setup_test_env()]] - `calls` [INFERRED]
- [[step3_save()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/login()_/_get_password_hash()