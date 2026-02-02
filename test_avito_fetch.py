
import asyncio
import requests
from app.services.avito_api_service import avito_api_service

async def test_fetch():
    print("Testing get_bookings...")
    item_id = 3792037514
    
    # 1. Standard call (repro)
    print("\n1. Standard call (with_unpaid=true):")
    try:
        data = await asyncio.to_thread(
            avito_api_service.get_bookings,
            item_id=item_id,
            date_start="2026-02-01",
            date_end="2026-02-10"
        )
        print("Success")
    except Exception as e:
        print(f"Failed: {e}")

    # 2. Without helper (direct request) to test params
    token = avito_api_service.get_access_token()
    base_url = "https://api.avito.ru/realty/v1/accounts/75878034/items/3792037514/bookings"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n2. Direct call without with_unpaid:")
    try:
        resp = requests.get(
            base_url,
            headers=headers,
            params={
                "date_start": "2026-02-01",
                "date_end": "2026-02-10"
            }
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n3. Direct call with with_unpaid=false:")
    try:
        resp = requests.get(
            base_url,
            headers=headers,
            params={
                "date_start": "2026-02-01",
                "date_end": "2026-02-10",
                "with_unpaid": "false" # bool string?
            }
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
