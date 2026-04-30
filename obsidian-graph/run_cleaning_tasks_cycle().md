---
source_file: "app\jobs\cleaning_tasks_job.py"
type: "code"
community: "cleaner.py / show_cleaner_menu()"
location: "L108"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/cleaner.py_/_show_cleaner_menu()
---

# run_cleaning_tasks_cycle()

## Connections
- [[cleaner_tasks_sync_now()]] - `calls` [INFERRED]
- [[cleaning_tasks_job.py]] - `contains` [EXTRACTED]
- [[generate_cleaning_tasks_for_tomorrow()]] - `calls` [EXTRACTED]
- [[notify_cleaners_about_tasks()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/cleaner.py_/_show_cleaner_menu()