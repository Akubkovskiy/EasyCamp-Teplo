---
type: community
cohesion: 0.06
members: 57
---

# houses.py / HouseUpdate

**Cohesion:** 0.06 - loosely connected
**Members:** 57 nodes

## Members
- [[BaseModel]] - code
- [[BookingBase]] - code - app\schemas\booking.py
- [[BookingOut]] - code - app\schemas\booking.py
- [[EditHouseStates]] - code - app\telegram\handlers\houses.py
- [[HouseBase]] - code - app\schemas\house.py
- [[HouseCreate]] - code - app\schemas\house.py
- [[HouseDiscountBase]] - code - app\schemas\house.py
- [[HouseDiscountCreate]] - code - app\schemas\house.py
- [[HouseDiscountOut]] - code - app\schemas\house.py
- [[HouseOut]] - code - app\schemas\house.py
- [[HousePriceBase]] - code - app\schemas\house.py
- [[HousePriceCreate]] - code - app\schemas\house.py
- [[HousePriceOut]] - code - app\schemas\house.py
- [[HousePriceUpdate]] - code - app\schemas\house.py
- [[HouseStates]] - code - app\telegram\handlers\houses.py
- [[HouseUpdate]] - code - app\schemas\house.py
- [[PriceStates]] - code - app\telegram\handlers\houses.py
- [[Settings]] - code - app\core\config.py
- [[StatesGroup]] - code
- [[booking.py]] - code - app\schemas\booking.py
- [[config.py]] - code - app\core\config.py
- [[confirm_delete_house()]] - code - app\telegram\handlers\houses.py
- [[create_house()_1]] - code - app\web\routers\house_web.py
- [[delete_house()_1]] - code - app\web\routers\house_web.py
- [[delete_house_price()]] - code - app\telegram\handlers\houses.py
- [[edit_house_form()]] - code - app\web\routers\house_web.py
- [[edit_house_menu()]] - code - app\telegram\handlers\houses.py
- [[execute_delete_house()]] - code - app\telegram\handlers\houses.py
- [[finish_editing()]] - code - app\telegram\handlers\houses.py
- [[house.py]] - code - app\schemas\house.py
- [[house_web.py]] - code - app\web\routers\house_web.py
- [[houses.py_1]] - code - app\telegram\handlers\houses.py
- [[list_house_prices()]] - code - app\telegram\handlers\houses.py
- [[list_houses()_1]] - code - app\telegram\handlers\houses.py
- [[list_houses()_2]] - code - app\web\routers\house_web.py
- [[new_house_form()]] - code - app\web\routers\house_web.py
- [[process_edit_base_price()]] - code - app\telegram\handlers\houses.py
- [[process_edit_capacity()]] - code - app\telegram\handlers\houses.py
- [[process_edit_desc()]] - code - app\telegram\handlers\houses.py
- [[process_edit_instr()]] - code - app\telegram\handlers\houses.py
- [[process_edit_name()]] - code - app\telegram\handlers\houses.py
- [[process_edit_photo()]] - code - app\telegram\handlers\houses.py
- [[process_edit_wifi()]] - code - app\telegram\handlers\houses.py
- [[process_house_capacity()]] - code - app\telegram\handlers\houses.py
- [[process_house_desc()]] - code - app\telegram\handlers\houses.py
- [[process_house_name()]] - code - app\telegram\handlers\houses.py
- [[process_price_amount()]] - code - app\telegram\handlers\houses.py
- [[process_price_date_from()]] - code - app\telegram\handlers\houses.py
- [[process_price_date_to()]] - code - app\telegram\handlers\houses.py
- [[process_price_label()]] - code - app\telegram\handlers\houses.py
- [[start_add_house()]] - code - app\telegram\handlers\houses.py
- [[start_add_price()]] - code - app\telegram\handlers\houses.py
- [[start_edit_field()]] - code - app\telegram\handlers\houses.py
- [[update_house()_1]] - code - app\web\routers\house_web.py
- [[view_house()]] - code - app\telegram\handlers\houses.py
- [[Создание дома (все поля в MVP)]] - rationale - app\web\routers\house_web.py
- [[Список сезонных цен для домика]] - rationale - app\telegram\handlers\houses.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/houses.py_/_HouseUpdate
SORT file.name ASC
```

## Connections to other communities
- 23 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 2 edges to [[_COMMUNITY_houses.py  get_short_description()]]
- 1 edge to [[_COMMUNITY_avito_webhook()  Verify HMAC-SHA256 signature.     Returns True if signature is valid OR if no s]]
- 1 edge to [[_COMMUNITY_str  settings.py]]
- 1 edge to [[_COMMUNITY_GlobalSetting  global_settings.py]]
- 1 edge to [[_COMMUNITY_cleaner_task_flow.py  get_all_users()]]
- 1 edge to [[_COMMUNITY_create.py  build_month_keyboard()]]

## Top bridge nodes
- [[BaseModel]] - degree 13, connects to 3 communities
- [[StatesGroup]] - degree 6, connects to 3 communities
- [[houses.py_1]] - degree 29, connects to 1 community
- [[HouseUpdate]] - degree 15, connects to 1 community
- [[HouseCreate]] - degree 9, connects to 1 community