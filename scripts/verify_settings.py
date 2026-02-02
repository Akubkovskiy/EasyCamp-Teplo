import asyncio
import os
import sys
import requests
from threading import Thread
import time
import uvicorn
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import GlobalSetting, User

# Ensure app is in path
sys.path.append(os.getcwd())

PORT = 8010
BASE_URL = f"http://localhost:{PORT}"

def run_server():
    uvicorn.run("app.main:app", port=PORT, log_level="error")

async def ensure_admin():
    async with AsyncSessionLocal() as db:
        # Create user if needed
        stmt = select(User).where(User.username == "admin_settings_test")
        res = await db.execute(stmt)
        u = res.scalar_one_or_none()
        if not u:
            from app.models import UserRole
            from app.core.security import get_password_hash
            db.add(User(
                username="admin_settings_test",
                hashed_password=get_password_hash("password123"),
                role=UserRole.OWNER,
                name="Settings Tester"
            ))
            await db.commit()
            print("[INFO] Created test admin user")

def test_settings_flow():
    # 1. Start Server
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(5)
    
    s = requests.Session()
    
    # 2. Login
    print("\n1. Login...")
    resp = s.post(f"{BASE_URL}/admin-web/login", data={
        "username": "admin_settings_test",
        "password": "password123"
    }, allow_redirects=True)
    
    resp.encoding = 'utf-8' # Force UTF-8
    
    if resp.status_code == 200 and ("Панель управления" in resp.text or "New Teplo Camp" in resp.text):
        print("[OK] Login successful")
    else:
        print(f"[FAIL] Login failed: {resp.status_code}")
        print("Response text preview:")
        print(resp.text[:500])
        return

    # 3. Get Settings Page
    print("\n2. Get Settings Page...")
    resp = s.get(f"{BASE_URL}/admin-web/settings")
    resp.encoding = 'utf-8'
    
    if resp.status_code == 200 and "Настройки проекта" in resp.text:
        print("[OK] Settings page loaded")
    else:
        print(f"[FAIL] Settings page failed: {resp.status_code}")
        return

    # 4. Update Settings
    print("\n3. Update Project Name...")
    new_name = f"Updated Project {int(time.time())}"
    data = {
        "project_name": new_name,
        "project_location": "Test City",
        "contact_phone": "+7000",
        "project_address": "Test Street 1",
        "contact_admin": "admin",
        "ai_enabled": "true",
        "spreadsheet_id": "TEST_SHEET"
    }
    resp = s.post(f"{BASE_URL}/admin-web/settings", data=data, allow_redirects=True)
    
    if resp.status_code == 200 and "Настройки успешно сохранены" in resp.text:
        print("[OK] Settings updated via Web")
    else:
        print(f"[FAIL] Update failed: {resp.status_code}")
        print(resp.text[:200])
        return

    # 5. Verify DB
    print("\n4. Verify DB...")
    async def verify_db():
        async with AsyncSessionLocal() as db:
            s_obj = await db.execute(select(GlobalSetting).where(GlobalSetting.key == "project_name"))
            val = s_obj.scalar_one_or_none()
            if val and val.value == new_name:
                print(f"[OK] DB Value verified: {val.value}")
            else:
                print(f"[FAIL] DB Value mismatch: {val.value if val else 'None'} != {new_name}")

    asyncio.run(verify_db())

if __name__ == "__main__":
    asyncio.run(ensure_admin())
    test_settings_flow()
