
import asyncio
import requests
import json
from datetime import datetime
from app.services.avito_api_service import avito_api_service

async def force_fix():
    token = avito_api_service.get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # HOUSE 3 (Item 3792037514) - Should be OPEN
    # User sees "pms" block. We want to wipe it.
    print("\n--- Fixing House 3 (Item 3792037514) ---")
    payload_h3 = {
        "intervals": [
            {
                "date_start": datetime.now().date().isoformat(),
                "date_end": "2026-07-30",
                "open": 1
            }
        ],
        "item_id": 3792037514,
        "source": "EasyCamp"
    }
    print(f"Sending payload: {json.dumps(payload_h3)}")
    try:
        resp = requests.post(
            "https://api.avito.ru/realty/v1/items/intervals",
            headers=headers,
            json=payload_h3
        )
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")
        
    # HOUSE 2 (Item 4719983476) - Should be BLOCKED Feb 1-7
    # We send interval starting Feb 7.
    print("\n--- Fixing House 2 (Item 4719983476) ---")
    payload_h2 = {
        "intervals": [
            {
                "date_start": "2026-02-07", # Start AFTER the booking
                "date_end": "2026-07-30",
                "open": 1
            }
        ],
        "item_id": 4719983476,
        "source": "EasyCamp"
    }
    print(f"Sending payload: {json.dumps(payload_h2)}")
    try:
        resp = requests.post(
            "https://api.avito.ru/realty/v1/items/intervals",
            headers=headers,
            json=payload_h2
        )
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(force_fix())
