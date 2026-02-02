import sqlite3
import os

DB_PATH = 'data/easycamp.db' # Correct path in Docker environment

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Update 'users' table
        print("Migrating 'users' table...")
        cursor.execute("PRAGMA table_info(users)")
        cols = [info[1] for info in cursor.fetchall()]
        if 'username' not in cols:
            print("Adding 'username' to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT UNIQUE")
        if 'hashed_password' not in cols:
            print("Adding 'hashed_password' to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN hashed_password TEXT")
        
        # 2. Update 'bookings' table
        print("Migrating 'bookings' table...")
        cursor.execute("PRAGMA table_info(bookings)")
        cols = [info[1] for info in cursor.fetchall()]
        if 'advance_amount' not in cols:
            print("Adding 'advance_amount' to bookings...")
            cursor.execute("ALTER TABLE bookings ADD COLUMN advance_amount DECIMAL(10, 2) DEFAULT 0")
        if 'commission' not in cols:
            print("Adding 'commission' to bookings...")
            cursor.execute("ALTER TABLE bookings ADD COLUMN commission DECIMAL(10, 2) DEFAULT 0")
        if 'prepayment_owner' not in cols:
            print("Adding 'prepayment_owner' to bookings...")
            cursor.execute("ALTER TABLE bookings ADD COLUMN prepayment_owner DECIMAL(10, 2) DEFAULT 0")
            
        # 3. Create 'global_settings' table
        print("Migrating 'global_settings' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT
            )
        """)
            
        conn.commit()
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
