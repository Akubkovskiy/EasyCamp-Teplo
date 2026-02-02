
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
        
        print("--- FILE SIZES ---")
        cmd = "docker exec easycamp_bot ls -lh /app/easycamp.db /app/data/easycamp.db"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        print("--- CHECKING BOOKINGS IN BOTH ---")
        script = """
import sqlite3
for path in ['/app/easycamp.db', '/app/data/easycamp.db']:
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute('SELECT count(*) FROM bookings')
        count = cur.fetchone()[0]
        print(f'{path}: {count} bookings')
        con.close()
    except Exception as e:
        print(f'{path}: Error {e}')
"""
        create_cmd = f"cat > /root/check_dbs.py <<EOF\n{script}\nEOF"
        client.exec_command(create_cmd)
        
        cmd_run = "docker cp /root/check_dbs.py easycamp_bot:/app/check_dbs.py && docker exec easycamp_bot python /app/check_dbs.py"
        stdin, stdout, stderr = client.exec_command(cmd_run)
        print(stdout.read().decode('utf-8', errors='ignore'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
