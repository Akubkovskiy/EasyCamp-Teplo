---
source_file: "app\jobs\cleaning_notifier.py"
type: "rationale"
community: "NotificationRule / NotificationService"
location: "L52"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/NotificationRule_/_NotificationService
---

# Проверяет выезды на ЗАВТРА и уведомляет уборщиц через Service

## Connections
- [[Booking]] - `uses` [INFERRED]
- [[NotificationRule]] - `uses` [INFERRED]
- [[check_and_notify_cleaners()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/NotificationRule_/_NotificationService