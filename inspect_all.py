
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
import sys
from app.core.config import settings
print(f'CWD: {os.getcwd()}')
print(f'CONFIG FILE: {__import__("app.core.config", fromlist=[""]).__file__}')
print(f'DATABASE_URL: {settings.database_url}')
print(f'ENV DATABASE_URL: {os.environ.get("DATABASE_URL")}')
print(f'FILE EXISTS /app/data/easycamp.db: {os.path.exists("/app/data/easycamp.db")}')
print(f'FILE EXISTS ./easycamp.db: {os.path.exists("./easycamp.db")}')
"""
        create_cmd = f"cat > /root/inspect_all.py <<EOF\n{script}\nEOF"
        client.exec_command(create_cmd)
        
        cmd_run = "docker cp /root/inspect_all.py easycamp_bot:/app/inspect_all.py && docker exec easycamp_bot python /app/inspect_all.py"
        stdin, stdout, stderr = client.exec_command(cmd_run)
        print(stdout.read().decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
