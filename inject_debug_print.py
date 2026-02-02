
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
        
        # Inject print statement
        cmd = "sed -i 's/settings = Settings(/print(f\"DEBUG: DATABASE_URL ENV is {os.environ.get(\\\"DATABASE_URL\\\")}\")\\nsettings = Settings(/' /root/easycamp-bot/app/core/config.py"
        client.exec_command(cmd)
        
        cmd2 = "sed -i 's/cleaning_notification_time=os.environ.get(\"CLEANING_NOTIFICATION_TIME\", \"20:00\"),/&\\n)\\nprint(f\"DEBUG: SETTINGS DATABASE_URL is {settings.database_url}\")/' /root/easycamp-bot/app/core/config.py"
        # Wait, the above sed is complex. Let's just append or use python to modify.
        
        print("Restarting bot to see debug output...")
        client.exec_command("cd /root/easycamp-bot && docker-compose restart app")
        
        time.sleep(5)
        print("--- APP LOGS (DEBUG) ---")
        stdin, stdout, stderr = client.exec_command("docker logs easycamp_bot | grep DEBUG")
        print(stdout.read().decode('utf-8', errors='ignore'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    import time
    main()
