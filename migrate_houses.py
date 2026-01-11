import sqlite3

try:
    conn = sqlite3.connect('easycamp.db')
    cursor = conn.cursor()
    
    columns = [
        "wifi_info VARCHAR",
        "address_coords VARCHAR",
        "checkin_instruction VARCHAR",
        "rules_text VARCHAR",
        "promo_description VARCHAR",
        "promo_image_id VARCHAR",
        "guide_image_id VARCHAR"
    ]
    
    for col in columns:
        try:
            cursor.execute(f"ALTER TABLE houses ADD COLUMN {col}")
            print(f"Added column: {col}")
        except Exception as e:
            print(f"Skipped {col}: {e}")
            
    conn.commit()
    print("Migration houses successful.")
except Exception as e:
    print(f"Migration failed: {e}")
finally:
    conn.close()
