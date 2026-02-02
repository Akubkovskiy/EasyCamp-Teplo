# scripts/utils/

Utility scripts for database setup and migrations.

> ⚠️ **WARNING**: These scripts modify the database directly. Always backup before running on production!

## Scripts

### `init_data.py`
Initialize database with default houses and settings.

```bash
cd /path/to/EasyCamp-Teplo
python scripts/utils/init_data.py
```

**Requires**: `DATABASE_URL` env variable or `.env` file.

---

### `migrate_houses.py`
Migrate house data from old schema to new.

```bash
python scripts/utils/migrate_houses.py
```

---

### `migrate_users.py`
Migrate user roles and permissions.

```bash
python scripts/utils/migrate_users.py
```

---

### `migrate_global_settings.py`
Migrate global settings (coordinates, rules, etc.) to new GlobalSettings table.

```bash
python scripts/utils/migrate_global_settings.py
```

---

## Usage Notes

1. **Always backup** the database before running any migration:
   ```bash
   cp easycamp.db easycamp.db.backup
   ```

2. Scripts should be run **from the project root** (not from scripts/utils/):
   ```bash
   cd /path/to/EasyCamp-Teplo
   python scripts/utils/<script>.py
   ```

3. Ensure `.env` is loaded or `DATABASE_URL` is set.
