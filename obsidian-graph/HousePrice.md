---
source_file: "app\models.py"
type: "code"
community: "BookingStatus / Booking"
location: "L72"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/BookingStatus_/_Booking
---

# HousePrice

## Connections
- [[Base_1]] - `inherits` [EXTRACTED]
- [[Base]] - `uses` [INFERRED]
- [[PricingService]] - `uses` [INFERRED]
- [[create_price()]] - `calls` [INFERRED]
- [[models.py]] - `contains` [EXTRACTED]
- [[Возвращает цену за ночь для конкретной даты.         Приоритет сезонная цена]] - `uses` [INFERRED]
- [[Проверяет загруженность на ближайшие дни.         Если домик свободен завтрапо]] - `uses` [INFERRED]
- [[Расчёт стоимости за весь период проживания.]] - `uses` [INFERRED]
- [[Расчёт цен с учётом сезонности и скидок.]] - `uses` [INFERRED]
- [[Сезонные цены для домика. Перекрывают base_price на указанный период.]] - `rationale_for` [EXTRACTED]
- [[Цена для отображения в каталоге (на сегодня).]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/BookingStatus_/_Booking