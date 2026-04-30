---
type: community
cohesion: 0.29
members: 8
---

# env.py / run_migrations_online()

**Cohesion:** 0.29 - loosely connected
**Members:** 8 nodes

## Members
- [[In this scenario we need to create an Engine     and associate a connection with]] - rationale - alembic\env.py
- [[Run migrations in 'offline' mode.      This configures the context with just a U]] - rationale - alembic\env.py
- [[Run migrations in 'online' mode.]] - rationale - alembic\env.py
- [[do_run_migrations()]] - code - alembic\env.py
- [[env.py]] - code - alembic\env.py
- [[run_async_migrations()]] - code - alembic\env.py
- [[run_migrations_offline()]] - code - alembic\env.py
- [[run_migrations_online()]] - code - alembic\env.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/env.py_/_run_migrations_online()
SORT file.name ASC
```
