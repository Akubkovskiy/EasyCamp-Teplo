import asyncio
import sys
import os
import requests
from threading import Thread
import uvicorn
import time
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import GlobalSetting

# Add project root to path
sys.path.append(os.getcwd())

def run_server():
    uvicorn.run("app.main:app", port=8008, log_level="error")

async def reset_state():
    async with AsyncSessionLocal() as db:
        # Reset init flag
        await db.execute(select(GlobalSetting).where(GlobalSetting.key == "initial_setup_done").execution_options(synchronize_session=False))
        # Clear settings
        # actually no need to clear settings, just overwrite
        
        # Manually set flag to false
        stmt = select(GlobalSetting).where(GlobalSetting.key == "initial_setup_done")
        res = await db.execute(stmt)
        s = res.scalar_one_or_none()
        if s:
            s.value = "false"
        else:
            db.add(GlobalSetting(key="initial_setup_done", value="false"))
            
        await db.commit()
        print("[INFO] Reset state completed")

async def test_wizard_flow():
    await reset_state()

    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(5) 
    
    base_url = "http://localhost:8008"
    s = requests.Session()

    # 1. Step 0: Check Secret
    print("\n1. Submit Secret...")
    resp = s.post(f"{base_url}/admin-web/setup/", data={"secret": "easycamp_secret"}, allow_redirects=False)
    if resp.status_code == 303 and "/setup/step1" in resp.headers.get("Location", ""):
        print(f"[OK] Secret accepted. Cookie: {s.cookies.get('setup_token')}")
    else:
        print(f"[FAIL] Secret check failed: {resp.status_code}")
        return

    # 2. Step 1: Get Form
    print("\n2. Get Step 1 Form...")
    resp = s.get(f"{base_url}/admin-web/setup/step1")
    if resp.status_code == 200 and "О проекте" in resp.text:
        print("[OK] Step 1 form loaded")
    else:
        print(f"[FAIL] Step 1 load failed: {resp.status_code}")
        return

    # 4. Step 1: Submit Data
    print("\n3. Submit Step 1 Data...")
    data = {
        "project_name": "New Teplo Camp",
        "project_location": "Dombay",
        "contact_phone": "+7 999 111-22-33",
        "project_address": "Mountain St. 1",
        "contact_admin": "@owner"
    }
    resp = s.post(f"{base_url}/admin-web/setup/step1", data=data, allow_redirects=False)
    if resp.status_code == 303 and "/setup/step2" in resp.headers.get("Location", ""):
        print("[OK] Step 1 saved, redirected to Step 2")
    else:
        print(f"[FAIL] Step 1 save failed: {resp.status_code} loc={resp.headers.get('Location')}")
        return

    # 4.5. Step 2: Submit Data
    print("\n3.5 Submit Step 2 Data...")
    data2 = {
        "ai_enabled": "true",
        "spreadsheet_id": "SHEET_ID_123"
    }
    resp = s.post(f"{base_url}/admin-web/setup/step2", data=data2, allow_redirects=False)
    if resp.status_code == 303 and "/setup/step3" in resp.headers.get("Location", ""):
        print("[OK] Step 2 saved, redirected to Step 3")
    else:
        print(f"[FAIL] Step 2 save failed: {resp.status_code} loc={resp.headers.get('Location')}")
        from pprint import pprint
        print("Resp text:")
        print(resp.text[:200])
        return

    # 4.8. Step 3: Create Admin
    print("\n3.8 Submit Step 3 (Admin)...")
    data3 = {
        "username": "owner_test",
        "password": "secure_password",
        "name": "Test Owner"
    }
    resp = s.post(f"{base_url}/admin-web/setup/step3", data=data3, allow_redirects=False)
    if resp.status_code == 303 and "/login?msg=setup_complete" in resp.headers.get("Location", ""):
        print("[OK] Step 3 saved, Setup Complete! Redirected to Login")
    else:
        print(f"[FAIL] Step 3 save failed: {resp.status_code} loc={resp.headers.get('Location')}")
        return

    # 5. Verify DB
    print("\n4. Verify DB storage...")
    async with AsyncSessionLocal() as db:
        # Check Project Name
        from typing import cast
        from app.models import User
        
        stmt = select(GlobalSetting).where(GlobalSetting.key == "project_name")
        res = await db.execute(stmt)
        setting = res.scalar_one_or_none()
        if setting and setting.value == "New Teplo Camp":
            print(f"[OK] DB Value 'project_name' = {setting.value}")
        else:
            print(f"[FAIL] DB verification failed. Found: {setting.value if setting else 'None'}")
        
        # Check User
        stmt = select(User).where(User.username == "owner_test")
        res = await db.execute(stmt)
        u = res.scalar_one_or_none()
        if u:
            print(f"[OK] Admin User Created: {u.username} (Role: {u.role})")
        else:
            print(f"[FAIL] Admin user not found")

    # 6. Finish (No explicit Finish endpoint anymore, Step 3 does it)

    # 5. Finish
    print("\n5. Finish Setup...")
    resp = s.get(f"{base_url}/admin-web/setup/finish", allow_redirects=False)
    if resp.status_code == 303:
        print("[OK] Finish redirected")
        if not s.cookies.get("setup_token"): # Should be deleted (expired) or empty
             # Requests session handling of deleted cookies is tricky, check header
             pass
    else:
        print(f"[FAIL] Finish failed: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_wizard_flow())
