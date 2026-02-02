
import paramiko
import sys
import os

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"

LOCAL_FILE = "docker-compose.yml"
REMOTE_FILE = "/root/easycamp-bot/docker-compose.yml"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        sftp = client.open_sftp()
        
        print(f"Uploading {LOCAL_FILE} -> {REMOTE_FILE}...")
        sftp.put(LOCAL_FILE, REMOTE_FILE)
        sftp.close()
        
        print("Recreating container with new config...")
        # Use down/up to clear 'KeyError: ContainerConfig' state in broken compose version
        cmd = "cd /root/easycamp-bot && docker-compose down && docker-compose up -d"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        print(out)
        if err: print(f"STDERR: {err}")
        
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
