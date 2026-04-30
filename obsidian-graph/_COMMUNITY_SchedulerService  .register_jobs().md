---
type: community
cohesion: 0.12
members: 18
---

# SchedulerService / .register_jobs()

**Cohesion:** 0.12 - loosely connected
**Members:** 18 nodes

## Members
- [[.__init__()_1]] - code - app\services\scheduler_service.py
- [[.get_jobs()]] - code - app\services\scheduler_service.py
- [[.pause()]] - code - app\services\scheduler_service.py
- [[.register_jobs()]] - code - app\services\scheduler_service.py
- [[.reload()]] - code - app\services\scheduler_service.py
- [[.resume()]] - code - app\services\scheduler_service.py
- [[.shutdown()]] - code - app\services\scheduler_service.py
- [[.start()]] - code - app\services\scheduler_service.py
- [[SchedulerService]] - code - app\services\scheduler_service.py
- [[scheduler_service.py]] - code - app\services\scheduler_service.py
- [[Возобновление всех задач]] - rationale - app\services\scheduler_service.py
- [[Остановка планировщика]] - rationale - app\services\scheduler_service.py
- [[Перезагрузка всех задач (для обновления настроек)]] - rationale - app\services\scheduler_service.py
- [[Получить список всех задач]] - rationale - app\services\scheduler_service.py
- [[Приостановка всех задач]] - rationale - app\services\scheduler_service.py
- [[Регистрация всех периодических задач]] - rationale - app\services\scheduler_service.py
- [[Сервис для управления периодическими задачами]] - rationale - app\services\scheduler_service.py
- [[Сервис планировщика для автоматической синхронизации]] - rationale - app\services\scheduler_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/SchedulerService_/_.register_jobs()
SORT file.name ASC
```
