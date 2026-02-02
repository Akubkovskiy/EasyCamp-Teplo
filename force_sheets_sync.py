
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
        
        print("--- DIAGNOSING ORM ---")
        
        # Python script to run inside container
        script = """
import logging
import sys
import asyncio
import os
from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import Booking
from sqlalchemy import select

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

print(f"DB URL: {settings.database_url}")

async def test():
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Booking)
            res = await session.execute(stmt)
            bookings = res.scalars().all()
            print(f"ORM Bookings Count: {len(bookings)}")
            for b in bookings:
                print(f" - ID: {b.id}, HouseID: {b.house_id}, Guest: {b.guest_name}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
"""
        
        # Escape for bash
        # actually, paramiko exec_command takes string.
        # We can write to a file on host and cat it into docker
        
        # 1. Write script to host temp file
        create_cmd = f"cat > /root/diag_script.py <<EOF\n{script}\nEOF"
        client.exec_command(create_cmd)
        
        # 2. Run inside docker
        cmd = "docker cp /root/diag_script.py easycamp_bot:/app/diag_script.py && docker exec easycamp_bot python /app/diag_script.py"
        
        stdin, stdout, stderr = client.exec_command(cmd)
        
        print(stdout.read().decode('utf-8', errors='ignore'))
        print(stderr.read().decode('utf-8', errors='ignore'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
