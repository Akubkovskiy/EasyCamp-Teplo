
import paramiko
import os
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
        sftp = client.open_sftp()
        
        # 1. Upload init script
        print("Uploading init_data.py...")
        local_script = "init_data.py"
        remote_script = "/root/easycamp-bot/init_data.py"
        sftp.put(local_script, remote_script)
        sftp.close()
        
        # 2. Run via Docker
        print("Running init_data.py inside Docker...")
        cmd = (
            "docker run --rm "
            "-v /root/easycamp-bot/data:/data "
            "-v /root/easycamp-bot/init_data.py:/init_data.py "
            "python:3.11-slim python /init_data.py"
        )
        
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. Restart bot
        print("Restarting bot...")
        client.exec_command("docker restart easycamp_bot")
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
