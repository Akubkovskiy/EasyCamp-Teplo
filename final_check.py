
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
        
        script = """
import sqlite3
import os
print(f'CWD: {os.getcwd()}')
for path in ['/app/easycamp.db', '/app/data/easycamp.db']:
    print(f'\\n--- {path} ---')
    if not os.path.exists(path):
        print('FILE NOT FOUND')
        continue
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute('SELECT count(*) FROM bookings')
        count = cur.fetchone()[0]
        print(f'Count: {count}')
        if count > 0:
            cur.execute('SELECT id, guest_name FROM bookings LIMIT 1')
            print(f'First booking: {cur.fetchone()}')
        con.close()
    except Exception as e:
        print(f'Error: {e}')
"""
        create_cmd = f"cat > /root/final_check.py <<EOF\n{script}\nEOF"
        client.exec_command(create_cmd)
        
        cmd_run = "docker cp /root/final_check.py easycamp_bot:/app/final_check.py && docker exec easycamp_bot python /app/final_check.py"
        stdin, stdout, stderr = client.exec_command(cmd_run)
        print(stdout.read().decode('utf-8', errors='ignore'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
