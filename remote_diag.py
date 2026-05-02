import paramiko
import sys

def check_remote():
    hostname = "176.126.103.245"
    username = "root"
    password = "21102016-Papa"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=hostname, username=username, password=password)
        
        print("--- DOCKER CONTAINERS (All) ---")
        stdin, stdout, stderr = client.exec_command("docker ps -a")
        print(stdout.read().decode())
        
        print("--- DOCKER PROJECTS ---")
        stdin, stdout, stderr = client.exec_command("find /root -name docker-compose.yml")
        print(stdout.read().decode())

        print("--- ROOT DIRECTORIES ---")
        stdin, stdout, stderr = client.exec_command("ls -F /root")
        print(stdout.read().decode())

        print("--- PYTHON PROCESSES ---")
        stdin, stdout, stderr = client.exec_command("ps -ef | grep python")
        print(stdout.read().decode())
        
        print("--- NETWORK CONNECTIONS (Telegram) ---")
        # Telegram API servers usually 149.154.167.0/24 or similar
        stdin, stdout, stderr = client.exec_command("ss -tpn | grep :443")
        print(stdout.read().decode())

    finally:
        client.close()

if __name__ == "__main__":
    check_remote()
