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
    uvicorn.run("app.main:app", port=8004, log_level="error")

async def reset_setup_flag():
    async with AsyncSessionLocal() as db:
        stmt = select(GlobalSetting).where(GlobalSetting.key == "initial_setup_done")
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = "false"
            await db.commit()
            print("[INFO] Reset 'initial_setup_done' to false")

async def test_setup_flow():
    # 0. Reset flag to ensure we trigger setup
    await reset_setup_flag()

    # 1. Start server
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(5) 
    
    base_url = "http://localhost:8004"

    # 2. Test Redirect on protected route
    print("\n1. Testing Redirect on Protected Route (/admin-web)...")
    try:
        resp = requests.get(f"{base_url}/admin-web", allow_redirects=False)
        if resp.status_code == 303 and "/admin-web/setup" in resp.headers.get("Location", ""):
            print("[OK] Redirected to /admin-web/setup")
        else:
            print(f"[FAIL] Expected 303 -> /setup, got {resp.status_code} loc={resp.headers.get('Location')}")
    except Exception as e:
        print(f"[FAIL] Request error: {e}")

    # 3. Test Allowlist (Static)
    print("\n2. Testing Allowlist (/admin-web/static)...")
    try:
        # Requesting a random static file
        resp = requests.get(f"{base_url}/admin-web/static/css/styles.css", allow_redirects=False)
        if resp.status_code != 303:
            print(f"[OK] Static file not redirected (Status: {resp.status_code})")
        else:
            print("[FAIL] Static file WAS redirected to setup!")
    except Exception as e:
        print(f"[FAIL] {e}")

    # 4. Test Setup Secret Failure
    print("\n3. Testing Setup Secret Failure...")
    try:
        resp = requests.post(f"{base_url}/admin-web/setup", data={"secret": "wrong_secret"})
        if resp.status_code == 403:
             print("[OK] Wrong secret rejected (403)")
        else:
             print(f"[FAIL] Expected 403, got {resp.status_code}")
    except Exception as e:
         print(f"[FAIL] {e}")

    # 5. Test Setup Success
    print("\n4. Testing Setup Success...")
    try:
        # Assuming dev default secret "easycamp_secret" or from env
        # In this env (based on previous edits) it might be "easycamp_secret" fallback
        secret = "easycamp_secret" 
        resp = requests.post(f"{base_url}/admin-web/setup", data={"secret": secret}, allow_redirects=False)
        
        if resp.status_code == 303 and "setup_complete" in resp.headers.get("Location", ""):
             print("[OK] Secrets accepted, redirected to login")
        else:
             print(f"[FAIL] Setup failed. Status: {resp.status_code}")
             print(resp.text[:200])

    except Exception as e:
         print(f"[FAIL] {e}")

    # 6. Verify Access After Setup
    print("\n5. Testing Access After Setup...")
    try:
        resp = requests.get(f"{base_url}/admin-web/login", allow_redirects=False)
        # Should be 200 OK (Login page), not redirect to setup
        if resp.status_code == 200:
            print("[OK] Login page accessible (Setup done)")
        elif resp.status_code == 303 and "setup" in resp.headers.get("Location", ""):
            print("[FAIL] Still redirected to setup!")
        else:
            print(f"[INFO] got {resp.status_code}")

    except Exception as e:
        print(f"[FAIL] {e}")

if __name__ == "__main__":
    asyncio.run(test_setup_flow())
