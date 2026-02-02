import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('easycamp.db')
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key VARCHAR PRIMARY KEY,
            value VARCHAR,
            description VARCHAR
        )
        """)
        
        # Insert default values
        defaults = [
            ("coords", "43.560731, 41.284236", "Общие координаты"),
            ("rules", "1. Заезд после 14:00...\n2. Тишина после 22:00...", "Общие правила"),
            ("bath_info", "Баня и чан доступны к заказу...", "Информация о бане")
        ]
        
        for key, val, desc in defaults:
            try:
                cursor.execute("INSERT INTO global_settings (key, value, description) VALUES (?, ?, ?)", (key, val, desc))
            except sqlite3.IntegrityError:
                pass # Already exists
                
        conn.commit()
        print("Migration global_settings successful.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
