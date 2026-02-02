import asyncio
import sys
import os
import requests
from threading import Thread
import uvicorn
import time

# Add project root to path
sys.path.append(os.getcwd())

def run_server():
    # Run slightly different port to verify_web_login (avoid conflict if zombie)
    # Also suppress logs
    uvicorn.run("app.main:app", port=8002, log_level="error")

async def test_auth_flow():
    print("[INFO] Testing Web Auth Flow...")
    
    # Start server
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(5) # Wait for startup
    
    base_url = "http://localhost:8002/admin-web"
    
    # 1. Login with WRONG password
    try:
        print("   1. Testing Invalid Login...")
        resp = requests.post(f"{base_url}/login", data={"username": "admin", "password": "wrong"})
        
        if resp.status_code == 401:
            print("[OK] Invalid login rejected (401)")
        else:
            print(f"[FAIL] Expected 401, got {resp.status_code}")
            
    except Exception as e:
        print(f"[FAIL] Invalid login request failed: {e}")

    # 2. Login with VALID password
    try:
        print("   2. Testing Valid Login...")
        # Don't follow redirects automatically to check cookie set
        resp = requests.post(
            f"{base_url}/login", 
            data={"username": "admin", "password": "12345"},
            allow_redirects=False
        )
        
        if resp.status_code == 303:
            print("[OK] Valid login redirected (303)")
            
            cookie = resp.cookies.get("admin_token")
            if cookie:
                print(f"[OK] Cookie 'admin_token' set: {cookie[:10]}...")
                
                # 3. Access Dashboard with Cookie
                print("   3. Testing Dashboard Access...")
                resp_dash = requests.get(f"{base_url}/", cookies={"admin_token": cookie})
                if resp_dash.status_code == 200:
                    if "Дашборд" in resp_dash.text and "Super Admin" in resp_dash.text:
                         print("[OK] Dashboard accessed. Content verified.")
                    else:
                         print("[FAIL] Dashboard content mismatch.")
                         print(resp_dash.text[:200])
                else:
                    print(f"[FAIL] Dashboard access failed: {resp_dash.status_code}")
                
            else:
                print("[FAIL] Cookie 'admin_token' NOT set")
                
        else:
            print(f"[FAIL] Expected 303, got {resp.status_code}")
            print(resp.text[:200])

    except Exception as e:
        print(f"[FAIL] Valid login request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
