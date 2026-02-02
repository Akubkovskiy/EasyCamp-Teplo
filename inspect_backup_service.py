
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
        
        print("--- CHECKING BACKUP SERVICE ON VPS ---")
        cmd_check = "cat /root/easycamp-bot/app/services/backup_service.py | grep -C 2 'def restore_latest_backup'"
        stdin, stdout, stderr = client.exec_command(cmd_check)
        out = stdout.read().decode('utf-8', errors='ignore')
        if out:
            print(f"FOUND FUNCTION:\n{out.encode('ascii', errors='ignore').decode()}")
        else:
            print("FUNCTION NOT FOUND in app/services/backup_service.py!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
