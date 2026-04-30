---
type: community
cohesion: 0.06
members: 52
---

# test_avito_overlap_guard.py / process_avito_booking()

**Cohesion:** 0.06 - loosely connected
**Members:** 52 nodes

## Members
- [[.__await__()]] - code - scripts\test_sync_logic.py
- [[.__call__()_2]] - code - scripts\test_sync_logic.py
- [[.test_enforce_mode_rejects_invalid_signature()]] - code - tests\test_webhook_integration.py
- [[.test_warn_mode_allows_invalid_signature()]] - code - tests\test_webhook_integration.py
- [[AsyncMock]] - code - scripts\test_sync_logic.py
- [[Fake Booking ORM object for overlap results.]] - rationale - tests\test_avito_overlap_guard.py
- [[Integration tests for Avito webhook endpoint using TestClient. These test the a]] - rationale - tests\test_webhook_integration.py
- [[Integration tests for webhook endpoint modes]] - rationale - tests\test_webhook_integration.py
- [[MagicMock]] - code
- [[Minimal Avito API booking payload (dict).]] - rationale - tests\test_avito_overlap_guard.py
- [[SMOKE TEST In enforce mode with invalid signature,          webhook should ret]] - rationale - tests\test_webhook_integration.py
- [[SMOKE TEST In warn mode with invalid signature,         webhook should return]] - rationale - tests\test_webhook_integration.py
- [[TestOverlapCondition]] - code - tests\test_avito_overlap_guard.py
- [[TestSyncPathOverlapGuard]] - code - tests\test_avito_overlap_guard.py
- [[TestWebhookIntegration]] - code - tests\test_webhook_integration.py
- [[TestWebhookPathOverlapGuard]] - code - tests\test_avito_overlap_guard.py
- [[Tests for Avito booking overlap guards (P0 hotfix).  Verifies that both ingest]] - rationale - tests\test_avito_overlap_guard.py
- [[Tests for BookingService.create_or_update_avito_booking overlap guard.]] - rationale - tests\test_avito_overlap_guard.py
- [[Tests for avito_sync_service.process_avito_booking overlap guard.]] - rationale - tests\test_avito_overlap_guard.py
- [[Verify the SQL overlap condition check_in  new_check_out AND check_out  new_c]] - rationale - tests\test_avito_overlap_guard.py
- [[_make_booking_data()]] - code - tests\test_avito_overlap_guard.py
- [[_make_existing_booking()]] - code - tests\test_avito_overlap_guard.py
- [[avito_fetch.py]] - code - app\telegram\handlers\avito_fetch.py
- [[avito_sync_job.py]] - code - app\jobs\avito_sync_job.py
- [[avito_sync_service.py]] - code - app\services\avito_sync_service.py
- [[fetch_from_avito()]] - code - app\telegram\handlers\avito_fetch.py
- [[map_avito_status()]] - code - app\services\avito_sync_service.py
- [[notify_new_bookings()]] - code - app\jobs\avito_sync_job.py
- [[notify_updated_bookings()]] - code - app\jobs\avito_sync_job.py
- [[process_avito_booking()]] - code - app\services\avito_sync_service.py
- [[sync_all_avito_items()]] - code - app\services\avito_sync_service.py
- [[sync_and_open_table()]] - code - app\telegram\handlers\bookings.py
- [[sync_avito_bookings()]] - code - app\services\avito_sync_service.py
- [[sync_avito_job()]] - code - app\jobs\avito_sync_job.py
- [[test_adjacent_dates_are_not_overlap()]] - code - tests\test_avito_overlap_guard.py
- [[test_avito_connection()]] - code - app\telegram\handlers\avito_fetch.py
- [[test_avito_overlap_guard.py]] - code - tests\test_avito_overlap_guard.py
- [[test_client()]] - code - tests\test_webhook_integration.py
- [[test_existing_booking_update_still_works()]] - code - tests\test_avito_overlap_guard.py
- [[test_new_booking_with_overlap_is_skipped()]] - code - tests\test_avito_overlap_guard.py
- [[test_new_booking_without_overlap_is_created()]] - code - tests\test_avito_overlap_guard.py
- [[test_overlap_condition()]] - code - tests\test_avito_overlap_guard.py
- [[test_sync_logic()]] - code - scripts\test_sync_logic.py
- [[test_sync_logic.py]] - code - scripts\test_sync_logic.py
- [[test_webhook_integration.py]] - code - tests\test_webhook_integration.py
- [[test_webhook_new_booking_with_overlap_blocked()]] - code - tests\test_avito_overlap_guard.py
- [[test_webhook_new_booking_without_overlap_created()]] - code - tests\test_avito_overlap_guard.py
- [[verify_local_bookings_in_avito()]] - code - app\jobs\avito_sync_job.py
- [[Обработчики для синхронизации с Avito API]] - rationale - app\telegram\handlers\avito_fetch.py
- [[Получить брони из Avito API]] - rationale - app\telegram\handlers\avito_fetch.py
- [[Скрипт для тестирования логики синхронизации (кэширование, TTL)]] - rationale - scripts\test_sync_logic.py
- [[Тестирование подключения к Avito API]] - rationale - app\telegram\handlers\avito_fetch.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_avito_overlap_guard.py_/_process_avito_booking()
SORT file.name ASC
```

## Connections to other communities
- 20 edges to [[_COMMUNITY_BookingStatus  Booking]]
- 5 edges to [[_COMMUNITY_str  settings.py]]
- 5 edges to [[_COMMUNITY_booking_service.py  create_or_update_avito_booking()]]
- 1 edge to [[_COMMUNITY_create.py  build_month_keyboard()]]
- 1 edge to [[_COMMUNITY_bookings.py  send_bookings_response()]]

## Top bridge nodes
- [[process_avito_booking()]] - degree 13, connects to 4 communities
- [[sync_and_open_table()]] - degree 5, connects to 3 communities
- [[avito_sync_service.py]] - degree 6, connects to 2 communities
- [[sync_avito_bookings()]] - degree 5, connects to 2 communities
- [[map_avito_status()]] - degree 4, connects to 2 communities