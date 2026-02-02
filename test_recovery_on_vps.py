
import paramiko
import time
import sys

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        
        # 1. Force Backup (to be sure we have something to restore)
        print("1. Forcing Backup to Google Drive...")
        cmd_backup = (
            "docker exec easycamp_bot python -c \""
            "import asyncio; "
            "from app.services.backup_service import backup_database_to_drive; "
            "asyncio.run(backup_database_to_drive())\""
        )
        stdin, stdout, stderr = client.exec_command(cmd_backup)
        out = stdout.read().decode('utf-8', errors='ignore')
        print(out)
        if "Backup failed" in out:
            print("❌ Backup failed! Aborting test.")
            return

        # 2. Simulate Disaster (Rename DB)
        print("2. Simulating Data Loss (Renaming DB)...")
        client.exec_command("mv /root/easycamp-bot/data/easycamp.db /root/easycamp-bot/data/easycamp.db.bak_test")
        
        # Verify it's gone
        stdin, stdout, stderr = client.exec_command("ls /root/easycamp-bot/data/easycamp.db")
        if "No such file" in stderr.read().decode():
            print("   -> Database file removed (renamed).")
        else:
            print("   -> ⚠️ File might still exist.")

        # 3. Restart Bot (Trigger Smart Recovery)
        print("3. Restarting Bot to trigger Smart Recovery...")
        client.exec_command("docker restart easycamp_bot")
        
        # 4. Watch Logs
        print("4. Watching logs for restore confirmation (max 30s)...")
        success = False
        for i in range(10):
            time.sleep(3)
            stdin, stdout, stderr = client.exec_command("docker logs --tail 20 easycamp_bot")
            logs = stdout.read().decode('utf-8', errors='ignore')
            # Look for specific log messages
            if "Restoring latest backup" in logs:
                print("   -> Found 'Restoring latest backup'...")
            if "Database restored successfully" in logs:
                print("   SUCCESS: 'Database restored successfully' found in logs!")
                success = True
                break
        
        if not success:
            print("Timeout: Did not see restore confirmation in logs.")
            print("Recent logs:\n" + logs.encode('ascii', errors='ignore').decode())
            
            # ROLLBACK
            print("Rolling back: Restoring original DB...")
            client.exec_command("mv /root/easycamp-bot/data/easycamp.db.bak_test /root/easycamp-bot/data/easycamp.db")
            client.exec_command("docker restart easycamp_bot")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
