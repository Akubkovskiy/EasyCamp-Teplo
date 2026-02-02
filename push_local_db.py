
import paramiko
import sys
import os

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"
LOCAL_DB = "easycamp.db"
REMOTE_DB = "/root/easycamp-bot/data/easycamp.db"

def main():
    if not os.path.exists(LOCAL_DB):
        print(f"❌ Local database '{LOCAL_DB}' not found!")
        return

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        sftp = client.open_sftp()
        
        print(f"Uploading {LOCAL_DB} -> {REMOTE_DB}...")
        sftp.put(LOCAL_DB, REMOTE_DB)
        print("Upload done.")
        sftp.close()
        
        print("Restarting bot to apply changes...")
        client.exec_command("docker restart easycamp_bot")
        print("Bot restarted.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
