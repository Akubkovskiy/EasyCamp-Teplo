---
source_file: "app\jobs\pricing_job.py"
type: "rationale"
community: "str / settings.py"
location: "L53"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/str_/_settings.py
---

# Синхронизирует текущие цены (base + сезонные + скидки) на Авито.     Запускаетс

## Connections
- [[PricingService]] - `uses` [INFERRED]
- [[avito_price_sync_job()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/str_/_settings.py