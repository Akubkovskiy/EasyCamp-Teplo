
import paramiko

HOST = "176.126.103.245"
USER = "root"
PASS = "21102016-Papa"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS)
        print("--- DB FILES ON HOST ---")
        stdin, stdout, stderr = client.exec_command("find /root/easycamp-bot -name '*.db' -ls")
        print(stdout.read().decode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
