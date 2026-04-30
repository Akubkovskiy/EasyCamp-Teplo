---
source_file: "app\jobs\pricing_job.py"
type: "code"
community: "str / settings.py"
location: "L83"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/str_/_settings.py
---

# pricing_cycle_job()

## Connections
- [[auto_discount_job()]] - `calls` [EXTRACTED]
- [[avito_price_sync_job()]] - `calls` [EXTRACTED]
- [[pricing_job.py]] - `contains` [EXTRACTED]
- [[run_pricing_cycle_now()]] - `calls` [INFERRED]
- [[Полный цикл сначала проверяем скидки, потом синхронизируем цены на Авито.]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/str_/_settings.py