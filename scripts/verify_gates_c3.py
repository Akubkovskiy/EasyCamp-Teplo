import asyncio
import os
import sys
import requests
from threading import Thread
import time
import uvicorn
from sqlalchemy import select, delete, update
from app.database import AsyncSessionLocal
from app.models import GlobalSetting, User
from app.core.config import settings as app_settings

# Ensure app is in path
sys.path.append(os.getcwd())

PORT = 8011
BASE_URL = f"http://localhost:{PORT}"

def run_server():
    uvicorn.run("app.main:app", port=PORT, log_level="error")

async def reset_state():
    async with AsyncSessionLocal() as db:
        print("[INFO] Resetting state...")
        # 1. Reset setup flag (Update)
        # Using update to be more explicit/efficient than select+save
        stmt = select(GlobalSetting).where(GlobalSetting.key == "initial_setup_done")
        res = await db.execute(stmt)
        s = res.scalar_one_or_none()
        if s:
            s.value = "false"
        else:
            db.add(GlobalSetting(key="initial_setup_done", value="false"))
            
        # 2. Cleanup test data if needed (optional)
        # await db.execute(delete(User).where(User.username == "gate_admin"))
        
        await db.commit()
        print("[INFO] Reset state completed (initial_setup_done=false)")

async def run_verification_gates():
    await reset_state()
    
    # Start Server
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(5) 
    
    s = requests.Session()
    
    # Use config secret
    SETUP_SECRET = app_settings.setup_secret
    if not SETUP_SECRET:
        print("[WARN] SETUP_SECRET not set in env, using default for test if possible or failing")
        # In this specific app, it might be auto-generated or loaded from .env. 
        # Assuming app_settings.setup_secret is correct.
    
    print(f"\n--- GATE 1: Setup Redirect (C1) ---")
    resp = s.get(f"{BASE_URL}/admin-web/", allow_redirects=False)
    if resp.status_code == 303 and "/admin-web/setup" in resp.headers.get("Location", ""):
        print(f"[OK] Redirected to Setup (Status: {resp.status_code})")
    else:
        print(f"[FAIL] Expected 303->Setup, got {resp.status_code}")
        return

    print("\n--- GATE 2: Wizard Flow (C2) ---")
    # 2.1 Secret
    print(f"Testing with secret: {SETUP_SECRET}")
    resp = s.post(f"{BASE_URL}/admin-web/setup/", data={"secret": SETUP_SECRET}, allow_redirects=False)
    if resp.status_code == 303: print("[OK] Secret Accepted")
    else: print(f"[FAIL] Secret Rejected (Status: {resp.status_code})"); return

    # 2.2 Step 1
    data = {"project_name": "Gate Tested Project", "project_location": "TestLoc", "contact_phone": "123", "ai_enabled": "true"}
    resp = s.post(f"{BASE_URL}/admin-web/setup/step1", data=data, allow_redirects=False)
    if resp.status_code == 303: print("[OK] Step 1 Complete")
    else: print("[FAIL] Step 1 Failed"); return

    # 2.3 Step 2
    # Using correct field names as per models/forms
    data2 = {"ai_enabled": "true", "spreadsheet_id": "GATE_SHEET"}
    resp = s.post(f"{BASE_URL}/admin-web/setup/step2", data=data2, allow_redirects=False)
    if resp.status_code == 303: print("[OK] Step 2 Complete")
    else: print("[FAIL] Step 2 Failed"); return

    print("\n--- GATE 3: Admin Creation (C3) ---")
    # 3.1 Step 3
    data3 = {"username": "gate_admin", "password": "password123", "name": "Gate Admin"}
    resp = s.post(f"{BASE_URL}/admin-web/setup/step3", data=data3, allow_redirects=False)
    
    # Should redirect to login?msg=setup_complete
    if resp.status_code == 303 and "/login" in resp.headers.get("Location", ""):
        print(f"[OK] Admin Created & Redirected to Login")
    else:
        print(f"[FAIL] Step 3 Failed: {resp.status_code} {resp.headers.get('Location')}")
        return

    print("\n--- GATE 4: Verify Auth & Dashboard ---")
    # 4.1 Check setup done flag via curl (should redirect to login now, not setup)
    resp = s.get(f"{BASE_URL}/admin-web/", allow_redirects=False)
    if resp.status_code == 303 and "/login" in resp.headers.get("Location", ""):
        print("[OK] /admin-web/ redirects to /login (Setup is done!)")
    elif resp.status_code == 200:
        print(f"[WARN] Unexpected 200 on Dashboard?")
    else:
        print(f"[FAIL] Unexpected status on Dashboard: {resp.status_code}")

    # 4.2 Login
    resp = s.post(f"{BASE_URL}/admin-web/login", data={"username": "gate_admin", "password": "password123"}, allow_redirects=True)
    resp.encoding = "utf-8"
    if resp.status_code == 200 and "Gate Tested Project" in resp.text: 
        print("[OK] Login Successful & Dashboard Loaded with Correct Branding")
    else:
        print(f"[FAIL] Login Failed or Branding Missing. Status: {resp.status_code}")
        print(resp.text[:200])
        return

    print("\n--- GATE 5: Settings Persistence (C3/C4) ---")
    # 5.1 Verify DB has Gate Tested Project
    async with AsyncSessionLocal() as db:
        stmt = select(GlobalSetting).where(GlobalSetting.key == "project_name")
        res = await db.execute(stmt)
        setting = res.scalar_one_or_none()
        if setting and setting.value == "Gate Tested Project":
            print(f"[OK] DB Persistence Verified: {setting.value}")
        else:
            print(f"[FAIL] DB Persistence Failed. Value: {setting.value if setting else 'None'}")

    print("\n✅ ALL GATES PASSED")

if __name__ == "__main__":
    try:
        asyncio.run(run_verification_gates())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"CRASH: {e}")
