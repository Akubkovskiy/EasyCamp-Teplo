
import sqlite3
import datetime

def check_booking():
    try:
        conn = sqlite3.connect('easycamp.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bookings WHERE id = 14")
        booking = cursor.fetchone()
        
        if booking:
            print(f"Booking found: {dict(booking)}")
        else:
            print("Booking #14 not found")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_booking()
