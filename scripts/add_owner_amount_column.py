import sqlite3
import os

db_path = "easycamp.db"

def add_column():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "prepayment_owner" not in columns:
            print("Adding prepayment_owner column...")
            cursor.execute("ALTER TABLE bookings ADD COLUMN prepayment_owner NUMERIC(10, 2) DEFAULT 0")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'prepayment_owner' already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()
