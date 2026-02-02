
import paramiko

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        script = """
import os
import sqlite3
from app.core.config import settings

print(f'--- APP STATUS ---')
print(f'DATABASE_URL from settings: {settings.database_url}')

# Find all .db files
print('\\n--- ALL DB FILES IN CONTAINER ---')
import subprocess
find_res = subprocess.run(['find', '/', '-name', 'easycamp.db', '-ls'], capture_output=True, text=True)
print(find_res.stdout)

# Check contents of candidate files
candidates = ['/app/data/easycamp.db', '/app/easycamp.db', '/data/easycamp.db']
for path in candidates:
    if os.path.exists(path):
        try:
            con = sqlite3.connect(path)
            cur = con.cursor()
            cur.execute('SELECT count(*) FROM bookings')
            count = cur.fetchone()[0]
            print(f'File {path}: {count} bookings')
            con.close()
        except Exception as e:
            print(f'File {path}: Error accessing - {e}')
    else:
        print(f'File {path}: DOES NOT EXIST')

"""
        create_cmd = f"cat > /root/final_debug.py <<EOF\n{script}\nEOF"
        client.exec_command(create_cmd)
        
        cmd_run = "docker cp /root/final_debug.py easycamp_bot:/app/final_debug.py && docker exec easycamp_bot python /app/final_debug.py"
        stdin, stdout, stderr = client.exec_command(cmd_run)
        print(stdout.read().decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
