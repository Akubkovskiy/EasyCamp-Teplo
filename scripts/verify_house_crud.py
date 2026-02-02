import asyncio
import os
import sys
import requests
from threading import Thread
import time
import uvicorn
from sqlalchemy import select, delete
from app.database import AsyncSessionLocal
from app.models import House, User

sys.path.append(os.getcwd())

PORT = 8012
BASE_URL = f"http://localhost:{PORT}"

def run_server():
    uvicorn.run("app.main:app", port=PORT, log_level="error")

async def setup_test_env():
    # Create Admin
    async with AsyncSessionLocal() as db:
        # User
        stmt = select(User).where(User.username == "crud_admin")
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            from app.models import UserRole
            from app.core.security import get_password_hash
            db.add(User(
                username="crud_admin",
                hashed_password=get_password_hash("password"),
                role=UserRole.OWNER,
                name="CRUD Tester"
            ))
            
        # Clean specific test house if exists
        stmt = select(House).where(House.name == "Test House A")
        res = await db.execute(stmt)
        h = res.scalar_one_or_none()
        if h:
            await db.delete(h)
            
        await db.commit()

async def verify_crud():
    await setup_test_env()
    
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(5)
    
    s = requests.Session()
    
    # Login
    print("\n1. Login...")
    s.post(f"{BASE_URL}/admin-web/login", data={"username": "crud_admin", "password": "password"})
    
    # Create
    print("\n2. Create House...")
    data = {
        "name": "Test House A",
        "description": "Created via Test",
        "capacity": 4,
        "wifi_info": "FreeWiFi",
        "checkin_instruction": "Key under mat"
    }
    resp = s.post(f"{BASE_URL}/admin-web/houses/", data=data)
    if resp.status_code == 200 and "Test House A" in resp.text: # Redirect followed to list
        print("[OK] House created and visible in list")
    else:
        print(f"[FAIL] Create failed: {resp.status_code}")
        return

    # Verify DB
    print("\n3. Verify DB...")
    async with AsyncSessionLocal() as db:
        stmt = select(House).where(House.name == "Test House A")
        res = await db.execute(stmt)
        h = res.scalar_one_or_none()
        if h and h.wifi_info == "FreeWiFi":
            print(f"[OK] DB Verified (ID={h.id})")
        else:
            print("[FAIL] Not found in DB")
            return
        
        house_id = h.id

    # Update
    print("\n4. Update House...")
    data_update = {
        "name": "Test House A", # Keep name
        "capacity": 10,
        "wifi_info": "NewWiFi",
        "checkin_instruction": "Code 1234"
    }
    resp = s.post(f"{BASE_URL}/admin-web/houses/{house_id}", data=data_update)
    if resp.status_code == 200:
        print("[OK] Update request success")
    
    # Verify Update
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(House).where(House.id == house_id))
        h = res.scalar_one()
        if h.capacity == 10 and h.wifi_info == "NewWiFi":
             print(f"[OK] DB Updated: Cap={h.capacity}, WiFi={h.wifi_info}")
        else:
             print(f"[FAIL] Update mismatch: {h.capacity}, {h.wifi_info}")

    print("\n✅ CRUD Verification Complete")

if __name__ == "__main__":
    asyncio.run(verify_crud())
