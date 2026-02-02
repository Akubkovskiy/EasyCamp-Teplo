
import paramiko
import sys
import os

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"

FILES_TO_UPDATE = [
    ("app/core/config.py", "/root/easycamp-bot/app/core/config.py"),
    ("docker-compose.yml", "/root/easycamp-bot/docker-compose.yml")
]

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        sftp = client.open_sftp()
        
        for local, remote in FILES_TO_UPDATE:
            if os.path.exists(local):
                print(f"Uploading {local} -> {remote}...")
                sftp.put(local, remote)
            else:
                print(f"Warning: Local file not found: {local}")
        
        sftp.close()
        
        print("Recreating container with fixed config...")
        # Force recreation to apply env var and code changes
        cmd = "cd /root/easycamp-bot && docker-compose down && docker-compose up -d"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        print(stdout.read().decode('utf-8', errors='ignore'))
        print(stderr.read().decode('utf-8', errors='ignore'))
        
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
