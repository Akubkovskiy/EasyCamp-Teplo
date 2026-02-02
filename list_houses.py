
import sqlite3

def check_houses():
    try:
        conn = sqlite3.connect('easycamp.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM houses")
        houses = cursor.fetchall()
        
        for house in houses:
            print(f"House: {dict(house)}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_houses()
