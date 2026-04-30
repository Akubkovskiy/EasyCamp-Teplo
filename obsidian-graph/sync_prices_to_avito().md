---
source_file: "app\services\avito_price_service.py"
type: "code"
community: "str / settings.py"
location: "L45"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/str_/_settings.py
---

# sync_prices_to_avito()

## Connections
- [[avito_price_service.py]] - `contains` [EXTRACTED]
- [[avito_price_sync_job()]] - `calls` [INFERRED]
- [[parse_avito_item_ids()]] - `calls` [EXTRACTED]
- [[str]] - `calls` [INFERRED]
- [[sync_house_avito_prices()]] - `calls` [INFERRED]
- [[Синхронизирует цены из базы на Авито.      Args         db Сессия БД]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/str_/_settings.py