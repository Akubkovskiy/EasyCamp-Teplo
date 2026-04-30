---
type: community
cohesion: 0.12
members: 21
---

# houses.py / get_short_description()

**Cohesion:** 0.12 - loosely connected
**Members:** 21 nodes

## Members
- [[HousePriceCalendarEntry]] - code - app\api\houses.py
- [[HousePublicOut]] - code - app\api\houses.py
- [[_find_house()]] - code - app\data\house_descriptions.py
- [[calculate_stay()]] - code - app\api\houses.py
- [[get_db()_1]] - code - app\api\houses.py
- [[get_full_description()]] - code - app\data\house_descriptions.py
- [[get_house_data()]] - code - app\data\house_descriptions.py
- [[get_short_description()]] - code - app\data\house_descriptions.py
- [[house_descriptions.py]] - code - app\data\house_descriptions.py
- [[house_price_calendar()]] - code - app\api\houses.py
- [[houses.py]] - code - app\api\houses.py
- [[list_houses()]] - code - app\api\houses.py
- [[Все данные по домику (short, full, capacity, area, aliases).]] - rationale - app\data\house_descriptions.py
- [[Ищем домик по имени точное совпадение → алиасы → подстрока.]] - rationale - app\data\house_descriptions.py
- [[Краткое описание (для карточек, каталога).]] - rationale - app\data\house_descriptions.py
- [[Описания домиков — единый источник для бота и API. Чтобы изменить описание — пр]] - rationale - app\data\house_descriptions.py
- [[Полное описание (для детальной карточки).]] - rationale - app\data\house_descriptions.py
- [[Прайс-календарь для конкретного домика (для виджета на сайте).]] - rationale - app\api\houses.py
- [[Публичный API для домиков и цен. Используется сайтом teplo-v-arkhyze для отобра]] - rationale - app\api\houses.py
- [[Расчёт стоимости проживания (для формы бронирования на сайте).]] - rationale - app\api\houses.py
- [[Список домиков с текущими ценами (для сайта).]] - rationale - app\api\houses.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/houses.py_/_get_short_description()
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 2 edges to [[_COMMUNITY_houses.py  HouseUpdate]]
- 2 edges to [[_COMMUNITY_guest.py  safe_edit()]]
- 1 edge to [[_COMMUNITY_create.py  build_month_keyboard()]]

## Top bridge nodes
- [[get_short_description()]] - degree 6, connects to 2 communities
- [[HousePriceCalendarEntry]] - degree 5, connects to 2 communities
- [[HousePublicOut]] - degree 5, connects to 2 communities
- [[get_full_description()]] - degree 4, connects to 1 community
- [[Публичный API для домиков и цен. Используется сайтом teplo-v-arkhyze для отобра]] - degree 3, connects to 1 community