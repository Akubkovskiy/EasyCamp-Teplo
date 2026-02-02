
import paramiko
import sys

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        print("--- INSPECTING DATABASE CONTENT ---")
        script = """
import sqlite3
from datetime import datetime
con = sqlite3.connect('/app/data/easycamp.db')
cur = con.cursor()

print('--- BOOKINGS ---')
cur.execute('SELECT id, check_in, check_out, guest_name, status, house_id FROM bookings')
rows = cur.fetchall()
for r in rows:
    print(r)

print('\\n--- HOUSES ---')
cur.execute('SELECT id, name FROM houses')
houses = cur.fetchall()
for h in houses:
    print(h)

con.close()
"""
        # Create temp script on host
        create_cmd = f"cat > /root/inspect_db.py <<EOF\n{script}\nEOF"
        client.exec_command(create_cmd)
        
        # Run inside docker
        cmd = "docker cp /root/inspect_db.py easycamp_bot:/app/inspect_db.py && docker exec easycamp_bot python /app/inspect_db.py"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        print(stdout.read().decode('utf-8', errors='ignore'))
        print(stderr.read().decode('utf-8', errors='ignore'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
