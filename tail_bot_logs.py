
import paramiko
import sys
import time

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        
        print("Tailing logs for 20 seconds. Please click 'All bookings' in the bot NOW...")
        # Get logs from the last 10 seconds and follow for 20
        cmd = "docker logs easycamp_bot --since 10s --follow"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Read for a fixed duration
        start_time = time.time()
        while time.time() - start_time < 20:
            if stdout.channel.recv_ready():
                line = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                print(line.encode('ascii', errors='ignore').decode(), end='')
            time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
