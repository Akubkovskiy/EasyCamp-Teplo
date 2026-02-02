import sqlite3

try:
    conn = sqlite3.connect('easycamp.db')
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR")
    conn.commit()
    print("Migration successful: Added phone column to users table.")
except Exception as e:
    print(f"Migration failed (maybe column exists?): {e}")
finally:
    conn.close()
