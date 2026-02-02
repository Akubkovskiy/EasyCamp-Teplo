
import sqlite3
import os

DB_PATH = '/data/easycamp.db'

def init_houses():
    print(f"Connecting to {DB_PATH}...")
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # ASCII names to be safe
        houses = [
            (1, "House 1 (Teplo)", "Description 1", 4),
            (2, "House 2 (Barn)", "Description 2", 6),
            (3, "House 3 (Scandi)", "Description 3", 4)
        ]
        
        count = 0
        for hid, name, desc, cap in houses:
            try:
                cur.execute("INSERT INTO houses (id, name, description, capacity) VALUES (?, ?, ?, ?)", (hid, name, desc, cap))
                print(f"Inserted House {hid}")
                count += 1
            except sqlite3.IntegrityError:
                print(f"House {hid} already exists - OK")
                
        con.commit()
        con.close()
        print(f"Success. Initialized {count} new houses.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    init_houses()
