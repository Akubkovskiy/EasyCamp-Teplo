import paramiko
import sys
import io
import os

# Force stdout/stderr to use UTF-8 as we are on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def deploy():
    hostname = "144.31.185.177"
    username = "root"
    key_path = os.path.expanduser("~/.ssh/id_ed25519_fin")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {hostname} via SSH key...")
        client.connect(hostname=hostname, username=username, key_filename=key_path)
        print("✅ Connected successfully!")

        project_dir = "/root/easycamp-bot"
        
        # 1. Check if it's a git repo
        print(f"Checking git status in {project_dir}...")
        stdin, stdout, stderr = client.exec_command(f"cd {project_dir} && git status")
        git_status_err = stderr.read().decode('utf-8', errors='replace')
        
        if "not a git repository" in git_status_err:
            print("Confirmed: Not a git repository. Initializing and syncing...")
            commands = [
                f"cd {project_dir}",
                "git init",
                "git remote add origin https://github.com/Akubkovskiy/EasyCamp-Teplo.git",
                "git fetch origin",
                "git reset --hard origin/main",
                "python3 scripts/remote_migrate_db.py" # Run migration
            ]
        else:
            print("Git repository detected. Syncing changes...")
            commands = [
                f"cd {project_dir}",
                "git fetch origin",
                "git reset --hard origin/main",
                "python3 scripts/remote_migrate_db.py" # Run migration
            ]
        
        # 2. Rebuild and restart
        commands.extend([
            "docker-compose stop",
            "docker-compose rm -f",
            "docker-compose up -d --build"
        ])
        
        full_command = " && ".join(commands)
        print(f"Executing deployment sequence...")
        
        stdin, stdout, stderr = client.exec_command(full_command)
        
        # Stream the output
        while True:
            line = stdout.readline()
            if not line:
                break
            print(f"OUT: {line.strip()}")
            
        err_output = stderr.read().decode('utf-8', errors='replace')
        if err_output:
            print(f"REMOTE LOGS/ERRORS:\n{err_output}")

        # 3. Final status check
        print("\nChecking container status...")
        stdin, stdout, stderr = client.exec_command(f"cd {project_dir} && docker-compose ps")
        print(stdout.read().decode('utf-8'))

        print("🚀 Deployment finished!")

    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    deploy()
