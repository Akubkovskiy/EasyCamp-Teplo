import asyncio
import sys
import os
import requests
from threading import Thread
import uvicorn

# Add project root to path
sys.path.append(os.getcwd())

def run_server():
    uvicorn.run("app.main:app", port=8001, log_level="error")

async def test_web_login():
    print("[INFO] Testing Web Login Endpoint...")
    
    # Start server in thread
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    
    # Wait for startup
    await asyncio.sleep(5)
    
    try:
        url = "http://localhost:8001/admin-web/login"
        print(f"   Requesting {url}...")
        resp = requests.get(url)
        
        if resp.status_code == 200:
            print("[OK] Status 200 OK")
            if "Вход в панель" in resp.text:
                print("[OK] Found 'Вход в панель' in HTML")
            else:
                print("[FAIL] HTML content mismatch")
                print(resp.text[:200])
        else:
            print(f"[FAIL] Status code: {resp.status_code}")
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_web_login())
