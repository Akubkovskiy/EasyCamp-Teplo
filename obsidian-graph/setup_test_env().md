---
source_file: "scripts\verify_house_crud.py"
type: "code"
community: "login() / get_password_hash()"
location: "L20"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/login()_/_get_password_hash()
---

# setup_test_env()

## Connections
- [[User]] - `calls` [INFERRED]
- [[get_password_hash()]] - `calls` [INFERRED]
- [[verify_crud()]] - `calls` [EXTRACTED]
- [[verify_house_crud.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/login()_/_get_password_hash()