import sqlite3
import os

DB_PATH = 'easycamp.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'advance_amount' in columns:
            print("Column 'advance_amount' already exists. Skipping.")
        else:
            print("Adding column 'advance_amount'...")
            cursor.execute("ALTER TABLE bookings ADD COLUMN advance_amount DECIMAL(10, 2) DEFAULT 0")
            print("Column added successfully.")
            
        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
