
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
        
        print("--- GREP SMART RECOVERY LOGS ---")
        cmd = "docker logs easycamp_bot 2>&1 | grep -E 'Smart Recovery|Restoring|Database restored|Backup successful'"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        out = stdout.read().decode('utf-8', errors='ignore')
        print(out.encode('ascii', errors='ignore').decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
