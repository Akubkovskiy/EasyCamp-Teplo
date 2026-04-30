---
source_file: "app\services\notification_service.py"
type: "code"
community: "NotificationRule / NotificationService"
location: "L18"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/NotificationRule_/_NotificationService
---

# NotificationRule

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[BookingStatus]] - `uses` [INFERRED]
- [[User]] - `uses` [INFERRED]
- [[UserRole]] - `uses` [INFERRED]
- [[check_and_notify_cleaners()]] - `calls` [INFERRED]
- [[check_and_notify_guests()]] - `calls` [INFERRED]
- [[notification_service.py]] - `contains` [EXTRACTED]
- [[Запуск проверки уведомлений для гостей]] - `uses` [INFERRED]
- [[Проверяет выезды на ЗАВТРА и уведомляет уборщиц через Service]] - `uses` [INFERRED]
- [[Сообщение в день выезда]] - `uses` [INFERRED]
- [[Сообщение в день заезда]] - `uses` [INFERRED]
- [[Сообщение за 2 дня до заезда]] - `uses` [INFERRED]
- [[Формирует клавиатуру подтверждения]] - `uses` [INFERRED]
- [[Формирует сообщение для уборщицы]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/NotificationRule_/_NotificationService