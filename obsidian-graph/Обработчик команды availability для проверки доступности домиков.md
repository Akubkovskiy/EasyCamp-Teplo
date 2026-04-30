---
source_file: "app\telegram\handlers\availability.py"
type: "rationale"
community: "create.py / build_month_keyboard()"
location: "L33"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/create.py_/_build_month_keyboard()
---

# Обработчик команды /availability для проверки доступности домиков

## Connections
- [[AvailabilityState]] - `uses` [INFERRED]
- [[BookingService]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[availability_command()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/create.py_/_build_month_keyboard()